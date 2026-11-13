"""The AssetGuard AI REST service.

The only place in the running system where models are loaded and risk is
scored. Sign in and sign out stand outside the guard; every other endpoint sits
behind it: first the caller is identified from their token, then their role is
checked against the area the requested path belongs to.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from google.genai import errors as genai_errors
from sqlalchemy.orm import Session

from access.password_security import create_session_token, verify_password_matches
from access.permissions import check_role_may_open_area, resolve_area_for_path, resolve_pages_for_role
from agentic import nodes
from agentic.graph import (
    build_initial_state,
    build_workflow,
    create_checkpoint_saver,
    resume_workflow_after_review,
    start_advisory_run,
)
from api.schemas import (
    AdvisoryRequest,
    CallBudgetResponse,
    ChatRequest,
    ChatResponse,
    ChatTurnResponse,
    FleetRiskRow,
    MachineNoteHistoryResponse,
    MachineProfileResponse,
    RepairJobResponse,
    ReviewDecisionRequest,
    ReviewDecisionResponse,
    RiskAssessmentResponse,
    SignedInUserResponse,
    SignInRequest,
    SignOutResponse,
)
from chat.conversation_memory import build_search_text, format_history_for_prompt, trim_conversation_history
from chat.machine_status_answer import build_machine_status_answer, build_unknown_machine_answer
from chat.manual_assistant import (
    LABEL_ANSWER,
    LABEL_MACHINE_ID,
    LABEL_QUESTION_TYPE,
    NONE_VALUE,
    answer_manual_question,
    check_answer_is_grounded,
    retrieve_manual_context,
)
from config import config
from persistence import repository
from persistence.database import create_database_directory, get_database_session
from tools.machine_data_tools import fetch_machine_note_history, fetch_machine_profile
from tools.prediction_tools import (
    build_model_input_row,
    classify_risk_band,
    detect_problem_type,
    predict_breakdown_probability,
    resolve_repair_priority,
    score_current_fleet,
)

# Prepared once at start-up. The models, fleet and notes are the ones the
# workflow steps already loaded, so the 130 MB risk model is held only once.
create_database_directory(config.DATABASE_DIRECTORY)
WORKFLOW = build_workflow(create_checkpoint_saver(config.CHECKPOINT_DATABASE_FILE))
SCORED_FLEET = score_current_fleet(nodes.BREAKDOWN_MODEL, nodes.CURRENT_FLEET, nodes.BREAKDOWN_SCHEMA)
RISK_THRESHOLDS = {"high": config.HIGH_RISK_THRESHOLD, "medium": config.MEDIUM_RISK_THRESHOLD}
FLEET_BAND_OPTIONS = [config.RISK_BAND_HIGH, config.RISK_BAND_MEDIUM, config.RISK_BAND_LOW, config.RISK_BAND_ALL]
RECENT_NOTE_COUNT = 5

DatabaseSession = Annotated[Session, Depends(get_database_session)]
SessionTokenHeader = Annotated[str, Header(alias=config.SESSION_TOKEN_HEADER)]


def _thread_config(thread_id):
    return {"configurable": {"thread_id": thread_id}}


def _machine_profile_or_404(machine_code):
    machine_profile = fetch_machine_profile(nodes.CURRENT_FLEET, machine_code)
    if not machine_profile:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Machine " + machine_code + " was not found")
    return machine_profile


def _repair_job_or_404(session, repair_job_id):
    repair_job = repository.fetch_repair_job_by_id(session, repair_job_id)
    if not repair_job:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Repair job " + repair_job_id + " was not found")
    return repair_job


# ---------------------------------------------------------------- sign in and the guard

def sign_in_user(sign_in_request: SignInRequest, session: DatabaseSession):
    account = repository.fetch_user_by_username(session, sign_in_request.username)
    # An unknown username and a wrong password get the same answer, so a stranger
    # cannot learn which accounts exist.
    if not account or not verify_password_matches(
            sign_in_request.password, account["password_hash"], account["password_salt"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, config.SIGN_IN_FAILED_MESSAGE)

    session_token = create_session_token()
    repository.update_user_session_token(session, account["username"], session_token)
    return {
        "username": account["username"],
        "display_name": account["display_name"],
        "role": account["role"],
        "session_token": session_token,
        "allowed_pages": resolve_pages_for_role(account["role"]),
    }


def sign_out_user(session: DatabaseSession, x_session_token: SessionTokenHeader):
    account = repository.fetch_user_by_session_token(session, x_session_token)
    if account:
        repository.update_user_session_token(session, account["username"], "")
    # The same answer whether or not the token was live.
    return {"signed_out": True}


def resolve_signed_in_user(session: DatabaseSession, x_session_token: SessionTokenHeader):
    account = repository.fetch_user_by_session_token(session, x_session_token)
    if not account:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sign in first: this session token is not recognised")
    return account


def require_area_access(request: Request, signed_in_user: Annotated[dict, Depends(resolve_signed_in_user)]):
    area_name = resolve_area_for_path(request.url.path, request.method)
    if not check_role_may_open_area(signed_in_user["role"], area_name):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Role " + signed_in_user["role"] + " may not open the " + (area_name or "unknown") + " area",
        )
    return signed_in_user


# ---------------------------------------------------------------- machines and fleet

def get_machine_profile(machine_code: str):
    return _machine_profile_or_404(machine_code)


def _score_machine(machine_profile):
    probability = predict_breakdown_probability(
        nodes.BREAKDOWN_MODEL, build_model_input_row(machine_profile, nodes.BREAKDOWN_SCHEMA))
    risk_band = classify_risk_band(probability, RISK_THRESHOLDS)
    return {
        "machine_code": machine_profile["machine_code"],
        "breakdown_probability": probability,
        "risk_band": risk_band,
        "priority": resolve_repair_priority(machine_profile["importance"], risk_band),
        "importance": machine_profile["importance"],
    }


def get_machine_risk(machine_code: str):
    return _score_machine(_machine_profile_or_404(machine_code))


def list_fleet_risk_summary(risk_band: Annotated[str, Query()]):
    if risk_band not in FLEET_BAND_OPTIONS:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "risk_band must be one of " + str(FLEET_BAND_OPTIONS))
    rows = SCORED_FLEET
    if risk_band != config.RISK_BAND_ALL:
        rows = rows[rows["risk_band"] == risk_band]
    return rows.to_dict(orient="records")


def get_machine_note_history(machine_code: str):
    note_history = fetch_machine_note_history(nodes.TECHNICIAN_NOTES, machine_code)
    problem_facts = detect_problem_type(nodes.PROBLEM_TYPE_MODEL, nodes.TEXT_VECTORIZER, note_history)
    return {
        "machine_code": machine_code,
        "note_count": problem_facts["note_count"],
        "detected_problem_type": problem_facts["problem_type"],
        "confidence": problem_facts["confidence"],
        "problem_votes": problem_facts["problem_votes"],
        "recent_notes": note_history[-RECENT_NOTE_COUNT:],
    }


# ---------------------------------------------------------------- advisory workflow

def create_advisory_run(advisory_request: AdvisoryRequest, session: DatabaseSession):
    # An unknown machine is refused before the workflow spends any model call.
    _machine_profile_or_404(advisory_request.machine_code)
    thread_id = "thread-" + uuid.uuid4().hex
    initial_state = build_initial_state(advisory_request.model_dump(), thread_id)
    paused_state = start_advisory_run(WORKFLOW, initial_state, _thread_config(thread_id))

    draft = paused_state.get("draft_repair_job") or {}
    if not draft.get("repair_job_id"):
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "The advisory run finished without a draft")
    return repository.fetch_repair_job_by_id(session, draft["repair_job_id"])


def list_repair_jobs_by_status(status_value: Annotated[str, Query()], session: DatabaseSession):
    if status_value not in config.REPAIR_JOB_STATUS_OPTIONS:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "status_value must be one of " + str(config.REPAIR_JOB_STATUS_OPTIONS))
    return repository.fetch_repair_jobs_by_status(session, status_value)


def get_repair_job_detail(repair_job_id: str, session: DatabaseSession):
    return _repair_job_or_404(session, repair_job_id)


def submit_review_decision(repair_job_id: str, decision_request: ReviewDecisionRequest, session: DatabaseSession):
    repair_job = _repair_job_or_404(session, repair_job_id)
    agent_run = repository.fetch_agent_run(session, repair_job["run_id"])
    if not agent_run:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "The run behind repair job " + repair_job_id + " was not found")
    if repair_job["status"] != config.REPAIR_JOB_STATUS_PENDING:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Repair job " + repair_job_id + " has already been decided: " + repair_job["status"])

    resume_workflow_after_review(WORKFLOW, _thread_config(agent_run["thread_id"]), decision_request.model_dump())
    # The workflow wrote through its own sessions, so read the final row fresh.
    session.expire_all()
    return repository.fetch_repair_job_by_id(session, repair_job_id)


def get_review_history(repair_job_id: str, session: DatabaseSession):
    repair_job = _repair_job_or_404(session, repair_job_id)
    return repository.fetch_decisions_for_run(session, repair_job["run_id"])


def get_call_budget(run_id: str, session: DatabaseSession):
    if not repository.fetch_agent_run(session, run_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Run " + run_id + " was not found")
    calls = repository.fetch_call_records_for_run(session, run_id)
    decisions = repository.fetch_decisions_for_run(session, run_id)
    rejected = any(decision["decision"] == config.REVIEW_DECISION_REJECT for decision in decisions)
    return {
        "run_id": run_id,
        "call_count": len(calls),
        "expected_call_count": config.EXPECTED_LLM_CALLS_PER_RUN - (1 if rejected else 0),
        "total_latency_milliseconds": sum(call["latency_milliseconds"] for call in calls),
        "calls": calls,
    }


# ---------------------------------------------------------------- manual chat

def ask_manual_assistant(
        chat_request: ChatRequest,
        signed_in_user: Annotated[dict, Depends(resolve_signed_in_user)],
        session: DatabaseSession):
    history = trim_conversation_history(
        [{"question": turn.question, "answer": turn.answer} for turn in chat_request.history],
        config.CHAT_HISTORY_TURN_LIMIT,
    )
    manual_context = retrieve_manual_context(nodes.MANUAL_SEARCH, build_search_text(history, chat_request.question))
    reply = answer_manual_question(chat_request.question, format_history_for_prompt(history), manual_context)

    question_type = reply[LABEL_QUESTION_TYPE].strip().upper()
    if question_type not in config.CHAT_TYPE_OPTIONS:
        question_type = config.CHAT_TYPE_OUT_OF_SCOPE
    machine_code = reply[LABEL_MACHINE_ID].strip()
    if machine_code.upper() == NONE_VALUE:
        machine_code = ""

    if question_type == config.CHAT_TYPE_MACHINE_STATUS:
        # A fact from the fleet data and the risk model, never from the manuals.
        source_documents = []
        machine_profile = fetch_machine_profile(nodes.CURRENT_FLEET, machine_code) if machine_code else {}
        if machine_profile:
            answer = build_machine_status_answer(machine_profile, _score_machine(machine_profile))
        else:
            answer = build_unknown_machine_answer(machine_code)
    elif (question_type == config.CHAT_TYPE_OUT_OF_SCOPE
          or not check_answer_is_grounded(question_type, manual_context["closest_distance"])
          or not reply[LABEL_ANSWER]):
        question_type = config.CHAT_TYPE_OUT_OF_SCOPE
        answer = config.CHAT_REFUSAL_MESSAGE
        source_documents = []
        machine_code = ""
    else:
        answer = reply[LABEL_ANSWER]
        source_documents = manual_context["source_documents"]

    repository.insert_chat_turn(session, {
        "username": signed_in_user["username"],
        "question": chat_request.question,
        "question_type": question_type,
        "answer": answer,
        "source_documents": ", ".join(source_documents),
        "machine_code": machine_code,
        "latency_milliseconds": reply["call_record"]["latency_milliseconds"],
    })
    return {
        "question_type": question_type,
        "answer": answer,
        "source_documents": source_documents,
        "chunks_searched": manual_context["chunk_count"],
    }


def list_recent_chat_turns(turn_limit: Annotated[int, Query()], session: DatabaseSession):
    if turn_limit < 1 or turn_limit > config.CHAT_AUDIT_MAX_ROWS:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "turn_limit must be between 1 and " + str(config.CHAT_AUDIT_MAX_ROWS))
    return repository.fetch_recent_chat_turns(session, turn_limit)


# ---------------------------------------------------------------- application

def create_api_application(application_title):
    """Attach every endpoint to a new application. Does not start a server."""
    application = FastAPI(
        title=application_title,
        description="Predictive maintenance and repair job advisory service for Meridian Heavy Industries.",
    )

    open_routes = APIRouter()
    open_routes.add_api_route("/auth/signin", sign_in_user, methods=["POST"], response_model=SignedInUserResponse)
    open_routes.add_api_route("/auth/signout", sign_out_user, methods=["POST"], response_model=SignOutResponse)

    guarded = APIRouter(dependencies=[Depends(require_area_access)])
    guarded.add_api_route("/machines/{machine_code}", get_machine_profile,
                          methods=["GET"], response_model=MachineProfileResponse)
    guarded.add_api_route("/machines/{machine_code}/risk", get_machine_risk,
                          methods=["GET"], response_model=RiskAssessmentResponse)
    guarded.add_api_route("/machines/{machine_code}/notes", get_machine_note_history,
                          methods=["GET"], response_model=MachineNoteHistoryResponse)
    guarded.add_api_route("/fleet/risk", list_fleet_risk_summary,
                          methods=["GET"], response_model=list[FleetRiskRow])
    guarded.add_api_route("/advisories", create_advisory_run, methods=["POST"],
                          response_model=RepairJobResponse, status_code=status.HTTP_201_CREATED)
    guarded.add_api_route("/repairjobs", list_repair_jobs_by_status,
                          methods=["GET"], response_model=list[RepairJobResponse])
    guarded.add_api_route("/repairjobs/{repair_job_id}", get_repair_job_detail,
                          methods=["GET"], response_model=RepairJobResponse)
    guarded.add_api_route("/repairjobs/{repair_job_id}/review", submit_review_decision,
                          methods=["POST"], response_model=RepairJobResponse)
    guarded.add_api_route("/repairjobs/{repair_job_id}/reviews", get_review_history,
                          methods=["GET"], response_model=list[ReviewDecisionResponse])
    guarded.add_api_route("/runs/{run_id}/calls", get_call_budget,
                          methods=["GET"], response_model=CallBudgetResponse)
    guarded.add_api_route("/chat/ask", ask_manual_assistant, methods=["POST"], response_model=ChatResponse)
    guarded.add_api_route("/audit/chat-turns", list_recent_chat_turns,
                          methods=["GET"], response_model=list[ChatTurnResponse])

    application.include_router(open_routes)
    application.include_router(guarded)
    application.add_exception_handler(genai_errors.APIError, _language_model_unavailable)
    return application


def _language_model_unavailable(request: Request, model_error: genai_errors.APIError):
    # The service is up but the model provider is not; say so rather than a bare 500.
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "The language model did not answer (" + str(model_error.code)
                           + "). Try again in a minute."},
    )
