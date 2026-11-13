import threading, secrets, re
from typing import Annotated
from fastapi import FastAPI, APIRouter, Depends, Header, HTTPException, Request, Query
from fastapi.responses import JSONResponse
from google.genai.errors import APIError
import httpx
from langgraph.types import Command
from config import config as c
from .schemas import *
from access.permissions import authorize_request
from access.password_security import hash_password
from persistence.database import session_factory
from persistence.models import UserAccount, AuthorisationReview, ChatTurn, AgentRun
from persistence.repository import *
from agentic.graph import build_workflow
from agentic import nodes
from tools.decision_tools import find_decision_refusal
from tools.request_data_tools import rank_review_queue, describe_request
from tools.prediction_tools import describe_expected_stay
from chat.conversation_memory import recall_conversation
from chat.authorisation_assistant import answer_from_documents
from chat.request_status_answer import answer_request_status
from sqlalchemy import true

review_workflow = build_workflow(c.CHECKPOINT_DATABASE_FILE)
request_details = {}
review_queue = []
for position, ref in enumerate(rank_review_queue(nodes.open_requests), 1):
    ctx = nodes.gather_request_context(ref)
    r = describe_request(ctx["request_profile"])
    s = ctx["screening"]
    detail = nodes.plain(
        dict(
            queue_position=position,
            request=r,
            request_documents=ctx["request_documents"],
            screening=s,
            evidence_findings=ctx["evidence_findings"],
            disagreements=ctx["disagreements"],
            likelihood=ctx["likelihood"],
            stay=ctx["stay"],
            stay_text=describe_expected_stay(
                ctx["stay"], ctx["request_profile"][c.SITE_OF_SERVICE_COLUMN]
            ),
        )
    )
    request_details[ref] = detail
    review_queue.append(
        dict(
            queue_position=position,
            request_reference=ref,
            service_code=s["service_code"],
            service_name=c.SERVICE_NAMES[s["service_code"]],
            urgency=r[c.URGENCY_COLUMN],
            site_of_service=r[c.SITE_OF_SERVICE_COLUMN],
            document_count=len(ctx["request_documents"]),
            **{k: s[k] for k in c.CRITERIA_COUNT_COLUMNS},
            screening=s["screening"],
            decisions_open=s["decisions_open"],
            **ctx["likelihood"],
            disagreement_count=len(ctx["disagreements"]),
        )
    )
request_locks = {r: threading.Lock() for r in request_details}
SessionTokenHeader = Annotated[str | None, Header(alias=c.SESSION_TOKEN_HEADER)]
SignedInUser = Annotated[dict, Depends(authorize_request)]
public_router = APIRouter()
guarded_router = APIRouter(dependencies=[Depends(authorize_request)])


@public_router.post("/auth/signin", response_model=SignedInUserResponse)
def sign_in_user(sign_in_request: SignInRequest):
    with session_factory.begin() as session:
        user = fetch_user_account(
            session, UserAccount.username == sign_in_request.username.strip()
        )
        if not user or not secrets.compare_digest(
            hash_password(sign_in_request.password, user["password_salt"]),
            user["password_hash"],
        ):
            raise HTTPException(401, c.SIGN_IN_FAILED_MESSAGE)
        token = secrets.token_urlsafe(c.SESSION_TOKEN_BYTES)
        update_session_token(session, user["username"], token)
    return {k: user[k] for k in ["username", "display_name", "role"]} | dict(
        session_token=token,
        pages=c.ROLE_PAGE_ACCESS[user["role"]],
        areas=c.ROLE_AREA_ACCESS[user["role"]],
    )


@public_router.post("/auth/signout", response_model=SignedOutResponse)
def sign_out_user(session_token: SessionTokenHeader = None):
    with session_factory.begin() as session:
        user = (
            fetch_user_account(session, UserAccount.session_token == session_token)
            if session_token
            else None
        )
        if not user:
            raise HTTPException(401, c.SIGN_IN_REQUIRED_MESSAGE)
        update_session_token(session, user["username"], None)
    return dict(username=user["username"], signed_out=True)


@guarded_router.get("/queue", response_model=list[QueueRow])
def list_review_queue(service_code: ServiceFilter):
    return [
        r
        for r in review_queue
        if service_code == c.QUEUE_SERVICE_ALL or r["service_code"] == service_code
    ]


@guarded_router.get("/queue/{request_reference}", response_model=RequestDetailResponse)
def get_request_detail(request_reference: str):
    if request_reference not in request_details:
        raise HTTPException(
            404, c.UNKNOWN_REQUEST_MESSAGE.format(request_reference=request_reference)
        )
    return request_details[request_reference]


def _reviews(condition):
    with session_factory() as session:
        return fetch_review_records(session, condition)


def _review(review_id):
    rows = _reviews(AuthorisationReview.review_id == review_id)
    if not rows:
        raise HTTPException(404, c.REVIEW_NOT_FOUND_MESSAGE)
    return rows[0]


@guarded_router.post("/reviews", status_code=201, response_model=ReviewRecordResponse)
def start_authorisation_review(
    review_request: ReviewRequest, signed_in_user: SignedInUser, request: Request
):
    ref = review_request.request_reference
    if ref not in request_details:
        raise HTTPException(
            404, c.UNKNOWN_REQUEST_MESSAGE.format(request_reference=ref)
        )
    with request_locks[ref]:
        if _reviews(AuthorisationReview.request_reference == ref):
            raise HTTPException(
                409, c.REQUEST_ALREADY_REVIEWED_MESSAGE.format(request_reference=ref)
            )
        thread = ref + "-" + secrets.token_hex(c.IDENTIFIER_HEX_LENGTH // 2).upper()
        request.state.opened_thread_id = thread
        review_workflow.invoke(
            dict(
                request_reference=ref,
                coordinator_request=review_request.coordinator_request,
                coordinator_id=signed_in_user["username"],
                thread_id=thread,
                llm_call_count=0,
            ),
            {"configurable": {"thread_id": thread}},
        )
        return _reviews(AuthorisationReview.request_reference == ref)[0]


@guarded_router.get("/reviews", response_model=list[ReviewRecordResponse])
def list_authorisation_reviews(
    status_value: Annotated[list[ReviewStatusValue], Query()],
):
    return _reviews(AuthorisationReview.status.in_(status_value))


@guarded_router.post(
    "/reviews/{review_id}/decision", response_model=ReviewRecordResponse
)
def submit_review_decision(
    review_id: str, decision_request: DecisionRequest, signed_in_user: SignedInUser
):
    review = _review(review_id)
    ref = review["request_reference"]
    if ref not in request_locks:
        raise ValueError(f"{review_id}: request no longer queued")
    with request_locks[ref]:
        review = _review(review_id)
        if review["status"] != c.REVIEW_STATUS_AWAITING:
            raise HTTPException(409, c.ALREADY_DECIDED_MESSAGE)
        cfg = {"configurable": {"thread_id": review["thread_id"]}}
        snapshot = review_workflow.get_state(cfg)
        state = snapshot.values
        if not state:
            raise ValueError(f"{review_id}: checkpoint missing")
        decision = dict(
            decision=decision_request.decision,
            decision_reason=decision_request.decision_reason,
            decided_by=signed_in_user["username"],
            decided_by_role=signed_in_user["role"],
        )
        refusal = find_decision_refusal(
            decision,
            state["screening"],
            state["request_profile"],
            state["coordinator_id"],
        )
        if refusal:
            raise HTTPException(409, refusal)
        pending = state.get("review_decision")
        if pending and pending != decision:
            raise HTTPException(409, c.DECISION_IN_PROGRESS_MESSAGE.format(**pending))
        review_workflow.invoke(None if pending else Command(resume=decision), cfg)
        return _review(review_id)


@guarded_router.get("/reviews/{review_id}/calls", response_model=CallBudgetResponse)
def get_call_budget(review_id: str):
    r = _review(review_id)
    with session_factory() as session:
        calls = fetch_llm_calls(session, r["run_id"])
    decision = r["decision"]
    if decision is None:
        state = review_workflow.get_state(
            {"configurable": {"thread_id": r["thread_id"]}}
        ).values
        if not state:
            raise ValueError(f"{review_id}: checkpoint missing")
        decision = (state.get("review_decision") or {}).get("decision")
    return dict(
        review_id=review_id,
        run_id=r["run_id"],
        call_count=len(calls),
        expected_call_count=(
            c.LLM_CALLS_BY_DECISION[decision]
            if decision
            else c.LLM_CALLS_BEFORE_DECISION
        ),
        total_latency_milliseconds=sum(x["latency_milliseconds"] for x in calls),
        calls=calls,
    )


@guarded_router.post("/chat/ask", response_model=ChatResponse)
def ask_authorisation_assistant(
    chat_request: ChatRequest, signed_in_user: SignedInUser
):
    written = chat_request.question
    matches = list(re.finditer(c.MEMBER_NUMBER_IN_TEXT_PATTERN, written))
    member = None
    if len(matches) == 1 and matches[0]["member_digits"].isdigit():
        member = "BWH-" + matches[0]["member_digits"]
    question = re.sub(
        c.MEMBER_NUMBER_IN_TEXT_PATTERN, c.CHAT_MEMBER_NUMBER_WITHHELD_TEXT, written
    )
    with session_factory() as session:
        conversation = recall_conversation(
            session, signed_in_user["username"], question
        )
    result = answer_from_documents(nodes.knowledge_collection, question, conversation)
    with session_factory.begin() as session:
        if result["question_type"] in c.CHAT_RECORD_TYPES:
            result["answer"] = answer_request_status(
                session,
                signed_in_user,
                nodes.open_requests,
                result["question_type"],
                result["request_reference"],
                member,
            )
        result["answer"] = re.sub(
            c.MEMBER_NUMBER_IN_TEXT_PATTERN,
            c.CHAT_MEMBER_NUMBER_WITHHELD_TEXT,
            result["answer"],
        )
        insert_chat_turn(
            session,
            dict(
                username=signed_in_user["username"],
                user_role=signed_in_user["role"],
                question_text=question,
                question_type=result["question_type"],
                request_reference=result["request_reference"],
                answer_text=result["answer"],
                source_documents=", ".join(result["source_documents"]),
                closest_distance=result["closest_distance"],
                was_refused=result["was_refused"],
            ),
        )
    return result


@guarded_router.get("/chat/turns", response_model=list[ChatTurnResponse])
def list_own_chat_turns(
    signed_in_user: SignedInUser,
    turn_limit: Annotated[int, Query(ge=1, le=c.CHAT_AUDIT_MAX_ROWS)],
):
    with session_factory() as session:
        return fetch_chat_turns(
            session, ChatTurn.username == signed_in_user["username"], turn_limit
        )


@guarded_router.get("/audit/chat-turns", response_model=list[ChatTurnResponse])
def list_recent_chat_turns(
    turn_limit: Annotated[int, Query(ge=1, le=c.CHAT_AUDIT_MAX_ROWS)],
):
    with session_factory() as session:
        return fetch_chat_turns(session, true(), turn_limit)


def report_failed_request(request: Request, failure: Exception):
    thread = getattr(request.state, "opened_thread_id", None)
    if thread:
        with session_factory.begin() as session:
            run = session.query(AgentRun).filter(AgentRun.thread_id == thread).first()
            if run:
                update_agent_run(
                    session,
                    run.run_id,
                    c.AGENT_RUN_STATUS_FAILED,
                    len(fetch_llm_calls(session, run.run_id)),
                )
    return JSONResponse(
        status_code=502,
        content={"detail": f"{request.method} {request.url.path}: {failure}"},
    )


service_application = FastAPI(title=c.API_TITLE)
service_application.include_router(public_router)
service_application.include_router(guarded_router)
for error in [ValueError, APIError, httpx.HTTPError]:
    service_application.add_exception_handler(error, report_failed_request)
