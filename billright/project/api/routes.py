"""Exposes the queue, the dispute detail, the assessment workflow, the decision, the call budget,
the chat and the audit trail over HTTP, behind a sign-in and access guard."""
import hmac
import secrets
from typing import Annotated

import pandas as pd
from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from langgraph.types import Command

from access.permissions import authorize_request
from access.password_security import hash_password
from agentic import nodes
from agentic.graph import build_workflow
from api.schemas import (
    AssessmentRequest,
    BillingDisputeResponse,
    CallBudgetResponse,
    ChatRequest,
    ChatResponse,
    ChatTurnResponse,
    DecisionRequest,
    DirectionFilter,
    DisputeDetailResponse,
    DisputeStatusValue,
    QueueRow,
    SignedInUserResponse,
    SignedOutResponse,
    SignInRequest,
)
from chat.billing_assistant import answer_from_documents
from chat.conversation_memory import recall_conversation
from chat.dispute_status_answer import answer_dispute_status
from config import config
from persistence import repository
from persistence.database import session_factory
from persistence.models import BillingDispute, ChatTurn, UserAccount
from tools.charge_tools import (
    build_charge_pieces,
    compare_with_billed,
    compute_corrected_charge,
    compute_redress,
    measure_usage,
    rank_dispute_queue,
)
from tools.dispute_data_tools import fetch_dispute_notes, fetch_dispute_profile
from tools.prediction_tools import build_cause_facts, build_rebill_facts, estimate_resolution_effort

# ------------------------------------------------------------------ built once
assessment_graph = build_workflow(config.CHECKPOINT_DATABASE_FILE)

_all_rebill_facts = build_rebill_facts(nodes.rebill_model, nodes.rebill_feature_names, nodes.open_disputes)
rebill_facts_by_reference = {
    reference: facts for reference, facts in
    zip(nodes.open_disputes[config.DISPUTE_REFERENCE_COLUMN], _all_rebill_facts)}

dispute_queue = [dict(row, **rebill_facts_by_reference[row[config.DISPUTE_REFERENCE_COLUMN]])
                 for row in rank_dispute_queue(nodes.open_disputes, nodes.tariff_schedules)]

SessionTokenHeader = Annotated[str | None, Header(alias=config.SESSION_TOKEN_HEADER)]


def _guard(request: Request, session_token: SessionTokenHeader = None):
    return authorize_request(request, session_token)


SignedInUser = Annotated[dict, Depends(_guard)]

public_router = APIRouter()
guarded_router = APIRouter(dependencies=[Depends(_guard)])


# ------------------------------------------------------------------ helpers
def _plain(value):
    """A gap in the queue row becomes None; everything else is carried as it is."""
    try:
        return None if pd.isna(value) else value
    except (TypeError, ValueError):
        return value


def _not_in_queue(reference):
    return HTTPException(status_code=404,
                         detail=config.DISPUTE_NOT_IN_QUEUE_MESSAGE.format(dispute_reference=reference))


def _assessment_record(assessment_id):
    session = session_factory()
    try:
        records = repository.fetch_dispute_records(session, BillingDispute.assessment_id == assessment_id)
    finally:
        session.close()
    return records[0] if records else None


def _as_response(record):
    """The stored amounts are exact text; the response carries them as Decimal."""
    return BillingDisputeResponse(**record).model_dump(mode="python")


# ------------------------------------------------------------------ public endpoints
@public_router.post("/auth/signin", response_model=SignedInUserResponse)
def sign_in_user(sign_in_request: SignInRequest):
    """Exchange a username and password for a session token."""
    session = session_factory()
    try:
        account = repository.fetch_user_account(session, UserAccount.username == sign_in_request.username)
        salt = account["password_salt"] if account else "0" * (2 * config.PASSWORD_SALT_BYTES)
        stored = account["password_hash"] if account else hash_password("unknown", salt)
        offered = hash_password(sign_in_request.password, salt)
        if account is None or not hmac.compare_digest(offered.encode(), stored.encode()):
            raise HTTPException(status_code=401, detail=config.SIGN_IN_FAILED_MESSAGE)
        token = secrets.token_hex(config.SESSION_TOKEN_BYTES)
        repository.update_session_token(session, account["username"], token)
    finally:
        session.close()
    return {"username": account["username"], "display_name": account["display_name"],
            "role": account["role"], "session_token": token,
            "pages": list(config.ROLE_PAGE_ACCESS[account["role"]]),
            "areas": list(config.ROLE_AREA_ACCESS[account["role"]])}


@public_router.post("/auth/signout", response_model=SignedOutResponse)
def sign_out_user(session_token: SessionTokenHeader = None):
    """End a session."""
    if not session_token:
        raise HTTPException(status_code=401, detail=config.SIGN_IN_REQUIRED_MESSAGE)
    session = session_factory()
    try:
        account = repository.fetch_user_account(session, UserAccount.session_token == session_token)
        if account is None:
            raise HTTPException(status_code=401, detail=config.SIGN_IN_REQUIRED_MESSAGE)
        repository.update_session_token(session, account["username"], None)
    finally:
        session.close()
    return {"username": account["username"], "signed_out": True}


# ------------------------------------------------------------------ guarded endpoints
@guarded_router.get("/queue", response_model=list[QueueRow])
def list_dispute_queue(direction: DirectionFilter):
    """Give the desk its ranked list of open disputes."""
    if direction == config.QUEUE_DIRECTION_ALL:
        return dispute_queue
    return [row for row in dispute_queue if row["direction"] == direction]


@guarded_router.get("/queue/{dispute_reference}", response_model=DisputeDetailResponse)
def get_dispute_detail(dispute_reference: str):
    """Show one dispute with every fact the assessment would work from."""
    if dispute_reference not in rebill_facts_by_reference:
        raise _not_in_queue(dispute_reference)
    profile = fetch_dispute_profile(nodes.open_disputes, dispute_reference)
    notes = fetch_dispute_notes(nodes.open_dispute_notes, dispute_reference)
    usage = measure_usage(profile)
    corrected = compute_corrected_charge(build_charge_pieces(profile, nodes.tariff_schedules), usage)
    comparison = compare_with_billed(profile, corrected["corrected_charge_gbp"])
    redress = compute_redress(profile, nodes.standard_payments)
    rebill = rebill_facts_by_reference[dispute_reference]
    cause = build_cause_facts(nodes.cause_model, notes)
    tariffs = []
    for piece in corrected["pieces"]:
        if piece["tariff"] not in tariffs:
            tariffs.append(piece["tariff"])
    if profile[config.BILLED_TARIFF_COLUMN] not in tariffs:
        tariffs.append(profile[config.BILLED_TARIFF_COLUMN])
    charge = {"tariff_schedules": {tariff: nodes.tariff_schedules[tariff] for tariff in tariffs},
              "usage": usage, "pieces": corrected["pieces"], "comparison": comparison, "redress": redress}
    effort = estimate_resolution_effort(nodes.effort_model, nodes.effort_feature_names, profile,
                                        rebill["rebill_band"], cause["dispute_category"],
                                        corrected["pieces"], comparison["money_at_stake_gbp"])
    return {"profile": {key: _plain(value) for key, value in profile.items()}, "note_texts": notes,
            "rebill": rebill, "cause": cause, "charge": charge, "effort": effort}


@guarded_router.post("/assessments", status_code=201, response_model=BillingDisputeResponse)
def start_dispute_assessment(assessment_request: AssessmentRequest, signed_in_user: SignedInUser,
                             request: Request):
    """Run the five assessing agents on one dispute and leave it waiting for a Revenue Controller."""
    reference = assessment_request.dispute_reference
    if reference not in rebill_facts_by_reference:
        raise _not_in_queue(reference)
    thread_id = reference + "-" + secrets.token_hex(config.IDENTIFIER_HEX_LENGTH)[:config.IDENTIFIER_HEX_LENGTH].upper()
    request.state.thread_id = thread_id
    finished = assessment_graph.invoke(
        {"dispute_reference": reference, "analyst_request": assessment_request.analyst_request,
         "analyst_id": signed_in_user["username"], "thread_id": thread_id, "llm_call_log": []},
        {"configurable": {"thread_id": thread_id}})
    return _as_response(_assessment_record(finished["assessment_id"]))


@guarded_router.get("/disputes", response_model=list[BillingDisputeResponse])
def list_disputes(status_value: Annotated[list[DisputeStatusValue], Query()]):
    """List assessments by status, for the decision queue and the audit trail."""
    session = session_factory()
    try:
        records = repository.fetch_dispute_records(session, BillingDispute.status.in_(status_value))
    finally:
        session.close()
    return [_as_response(record) for record in records]


@guarded_router.post("/disputes/{assessment_id}/decision", response_model=BillingDisputeResponse)
def submit_controller_decision(assessment_id: str, decision_request: DecisionRequest,
                               signed_in_user: SignedInUser):
    """Record the decision and resume the paused run."""
    record = _assessment_record(assessment_id)
    if record is None:
        raise HTTPException(status_code=404, detail=config.ASSESSMENT_NOT_FOUND_MESSAGE)
    if record["analyst_id"] == signed_in_user["username"]:
        raise HTTPException(status_code=403, detail=config.OWN_ASSESSMENT_REFUSED_MESSAGE)
    if record["decision"] is not None or record["status"] != config.DISPUTE_STATUS_PENDING:
        raise HTTPException(status_code=409, detail=config.ALREADY_DECIDED_MESSAGE)
    configurable = {"configurable": {"thread_id": record["thread_id"]}}
    held = assessment_graph.get_state(configurable)
    in_progress = (held.values or {}).get("controller_decision")
    if in_progress and in_progress.get("decision") != decision_request.decision:
        raise HTTPException(status_code=409, detail=config.DECISION_IN_PROGRESS_MESSAGE.format(
            decision=in_progress["decision"]))
    if in_progress:
        assessment_graph.invoke(None, configurable)          # finish recording the same decision
    else:
        assessment_graph.invoke(Command(resume={
            "decision": decision_request.decision, "decided_by": signed_in_user["display_name"],
            "decided_by_role": signed_in_user["role"],
            "decision_reason": decision_request.decision_reason}), configurable)
    return _as_response(_assessment_record(assessment_id))


@guarded_router.get("/disputes/{assessment_id}/calls", response_model=CallBudgetResponse)
def get_call_budget(assessment_id: str):
    """Show every language model call an assessment's run made, against the number allowed."""
    record = _assessment_record(assessment_id)
    if record is None:
        raise HTTPException(status_code=404, detail=config.ASSESSMENT_NOT_FOUND_MESSAGE)
    session = session_factory()
    try:
        calls = repository.fetch_llm_calls(session, record["run_id"])
    finally:
        session.close()
    expected = (config.LLM_CALLS_BEFORE_DECISION if record["decision"] is None
                else config.LLM_CALLS_BY_DECISION[record["decision"]])
    return {"assessment_id": assessment_id, "run_id": record["run_id"], "call_count": len(calls),
            "expected_call_count": expected,
            "total_latency_milliseconds": sum(call["latency_milliseconds"] for call in calls),
            "calls": calls}


@guarded_router.post("/chat/ask", response_model=ChatResponse)
def ask_billing_assistant(chat_request: ChatRequest, signed_in_user: SignedInUser):
    """Answer one question from the documents, or refuse, and record the exchange."""
    session = session_factory()
    try:
        conversation = recall_conversation(session, signed_in_user["username"], chat_request.question)
        result = answer_from_documents(nodes.knowledge_collection, chat_request.question, conversation)
        if result["question_type"] == config.CHAT_TYPE_DISPUTE_STATUS:
            result.update(answer_dispute_status(session, nodes.open_disputes, signed_in_user["role"],
                                                result["dispute_reference"]))
        repository.insert_chat_turn(session, {
            "username": signed_in_user["username"], "user_role": signed_in_user["role"],
            "question_text": chat_request.question, "question_type": result["question_type"],
            "dispute_reference": result["dispute_reference"], "answer_text": result["answer"],
            "source_documents": ", ".join(result["source_documents"]),
            "closest_distance": result["closest_distance"], "was_refused": result["was_refused"]})
    finally:
        session.close()
    return {key: result[key] for key in ("question_type", "dispute_reference", "answer",
                                         "source_documents", "was_refused")}


@guarded_router.get("/chat/turns", response_model=list[ChatTurnResponse])
def list_own_chat_turns(signed_in_user: SignedInUser,
                        turn_limit: Annotated[int, Query(ge=1, le=config.CHAT_AUDIT_MAX_ROWS)]):
    """Give a person their own conversation back, for the chat page."""
    session = session_factory()
    try:
        return repository.fetch_chat_turns(session, ChatTurn.username == signed_in_user["username"], turn_limit)
    finally:
        session.close()


@guarded_router.get("/audit/chat-turns", response_model=list[ChatTurnResponse])
def list_recent_chat_turns(turn_limit: Annotated[int, Query(ge=1, le=config.CHAT_AUDIT_MAX_ROWS)]):
    """Give the audit trail every recent question, whoever asked it."""
    session = session_factory()
    try:
        return repository.fetch_chat_turns(session, ChatTurn.turn_id > 0, turn_limit)
    finally:
        session.close()


# ------------------------------------------------------------------ one handler for every failure
def report_failed_request(request, failure):
    """Turn every failure into one reply the dashboard can show, and close a failed run."""
    thread_id = getattr(request.state, "thread_id", None)
    if thread_id:
        try:
            held = assessment_graph.get_state({"configurable": {"thread_id": thread_id}})
            run_id = (held.values or {}).get("run_id")
            if run_id:
                session = session_factory()
                try:
                    calls = repository.fetch_llm_calls(session, run_id)
                    repository.update_agent_run(session, run_id, config.AGENT_RUN_STATUS_FAILED, len(calls))
                finally:
                    session.close()
        except Exception:
            pass
    return JSONResponse(status_code=502, content={
        "detail": f"{request.method} {request.url.path} failed: {failure}"})


service_application = FastAPI(title=config.API_TITLE)
service_application.include_router(public_router)
service_application.include_router(guarded_router)
service_application.add_exception_handler(Exception, report_failed_request)
