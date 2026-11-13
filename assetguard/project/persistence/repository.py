"""Every save and read against the application tables.

Each function is handed an open session and never opens or closes one. Rows go
out as plain dictionaries so nothing outside this module depends on table shape.
Database timestamps have one-second resolution, so lists ordered by time use
the row id as a tie-breaker.
"""

from sqlalchemy import func

from config import config
from persistence.models import (
    AgentRun,
    ChatTurnRecord,
    LlmCallRecord,
    RepairJobDraft,
    ReviewDecision,
    UserAccount,
)

RUN_FIELDS = ["run_id", "thread_id", "machine_code", "request_text", "status"]
REPAIR_JOB_FIELDS = [
    "repair_job_id", "run_id", "machine_code", "machine_type", "breakdown_probability",
    "risk_band", "problem_type", "priority", "estimated_downtime_hours", "permit_required",
    "procedure_reference", "parts_required", "task_steps", "safety_notes", "proposed_window",
    "source_documents", "job_summary", "scheduling_note", "status",
]
REVIEW_OUTCOME_FIELDS = ["job_summary", "task_steps", "changes_applied", "status"]
DECISION_FIELDS = ["run_id", "repair_job_id", "decision", "reviewer_name", "feedback_text", "reviewed_draft"]
CALL_FIELDS = ["agent_name", "model_name", "prompt_characters", "response_characters", "latency_milliseconds"]
ACCOUNT_FIELDS = ["username", "display_name", "role", "password_hash", "password_salt"]
CHAT_FIELDS = [
    "username", "question", "question_type", "answer", "source_documents",
    "machine_code", "latency_milliseconds",
]


def _as_text(timestamp):
    return "" if timestamp is None else timestamp.isoformat(sep=" ")


def _save(session, row):
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _single_row(session, model, column, value):
    row = session.query(model).filter(column == value).one_or_none()
    if row is None:
        raise LookupError(model.__tablename__ + " has no row with " + column.key + " " + repr(value))
    return row


# ---------------------------------------------------------------- agent runs

def insert_agent_run(session, run_record):
    row = _save(session, AgentRun(**{name: run_record[name] for name in RUN_FIELDS}))
    return row.run_id


def update_agent_run_status(session, run_id, status_value):
    row = _single_row(session, AgentRun, AgentRun.run_id, run_id)
    row.status = status_value
    if status_value == config.AGENT_RUN_STATUS_COMPLETE:
        row.completed_at = session.query(func.now()).scalar()
    session.commit()
    return run_id


def fetch_agent_run(session, run_id):
    row = session.query(AgentRun).filter(AgentRun.run_id == run_id).one_or_none()
    if row is None:
        return {}
    return {
        "run_id": row.run_id,
        "thread_id": row.thread_id,
        "machine_code": row.machine_code,
        "request_text": row.request_text,
        "status": row.status,
        "started_at": _as_text(row.started_at),
        "completed_at": _as_text(row.completed_at),
    }


# ---------------------------------------------------------------- repair jobs

def insert_repair_job_draft(session, repair_job_record):
    values = {name: repair_job_record[name] for name in REPAIR_JOB_FIELDS}
    values["changes_applied"] = ""
    row = _save(session, RepairJobDraft(**values))
    return row.repair_job_id


def apply_review_outcome(session, repair_job_id, final_repair_job):
    """Write back only the four finalizer fields; the evidence columns are never touched."""
    row = _single_row(session, RepairJobDraft, RepairJobDraft.repair_job_id, repair_job_id)
    for name in REVIEW_OUTCOME_FIELDS:
        setattr(row, name, final_repair_job[name])
    session.commit()
    return repair_job_id


def update_repair_job_status(session, repair_job_id, status_value):
    row = _single_row(session, RepairJobDraft, RepairJobDraft.repair_job_id, repair_job_id)
    row.status = status_value
    session.commit()
    return repair_job_id


def build_repair_job_dictionary(repair_job_row):
    record = {name: getattr(repair_job_row, name) for name in REPAIR_JOB_FIELDS}
    record["changes_applied"] = repair_job_row.changes_applied
    record["created_at"] = _as_text(repair_job_row.created_at)
    return record


def fetch_repair_job_by_id(session, repair_job_id):
    row = session.query(RepairJobDraft).filter(RepairJobDraft.repair_job_id == repair_job_id).one_or_none()
    return {} if row is None else build_repair_job_dictionary(row)


def fetch_repair_jobs_by_status(session, status_value):
    rows = (
        session.query(RepairJobDraft)
        .filter(RepairJobDraft.status == status_value)
        .order_by(RepairJobDraft.created_at.desc(), RepairJobDraft.id.desc())
        .all()
    )
    return [build_repair_job_dictionary(row) for row in rows]


# ---------------------------------------------------------------- review decisions

def insert_review_decision(session, decision_record):
    row = _save(session, ReviewDecision(**{name: decision_record[name] for name in DECISION_FIELDS}))
    return row.id


def build_decision_dictionary(decision_row):
    record = {"id": decision_row.id}
    record.update({name: getattr(decision_row, name) for name in DECISION_FIELDS})
    record["decided_at"] = _as_text(decision_row.decided_at)
    return record


def fetch_decisions_for_run(session, run_id):
    rows = (
        session.query(ReviewDecision)
        .filter(ReviewDecision.run_id == run_id)
        .order_by(ReviewDecision.decided_at, ReviewDecision.id)
        .all()
    )
    return [build_decision_dictionary(row) for row in rows]


# ---------------------------------------------------------------- language model calls

def insert_llm_call_record(session, call_record, run_id):
    values = {name: call_record[name] for name in CALL_FIELDS}
    for name in ("prompt_characters", "response_characters", "latency_milliseconds"):
        values[name] = int(values[name])
    row = _save(session, LlmCallRecord(run_id=run_id, **values))
    return row.id


def build_call_dictionary(call_row):
    record = {"id": call_row.id, "run_id": call_row.run_id}
    record.update({name: getattr(call_row, name) for name in CALL_FIELDS})
    record["called_at"] = _as_text(call_row.called_at)
    return record


def fetch_call_records_for_run(session, run_id):
    rows = (
        session.query(LlmCallRecord)
        .filter(LlmCallRecord.run_id == run_id)
        .order_by(LlmCallRecord.called_at, LlmCallRecord.id)
        .all()
    )
    return [build_call_dictionary(row) for row in rows]


# ---------------------------------------------------------------- user accounts

def insert_user_account(session, account_record):
    """Create an account, or leave an existing one with this username exactly as it is."""
    existing = session.query(UserAccount).filter(UserAccount.username == account_record["username"]).one_or_none()
    if existing is not None:
        return existing.username
    values = {name: account_record[name] for name in ACCOUNT_FIELDS}
    row = _save(session, UserAccount(session_token="", **values))
    return row.username


def build_user_dictionary(user_row):
    return {
        "username": user_row.username,
        "display_name": user_row.display_name,
        "role": user_row.role,
        "password_hash": user_row.password_hash,
        "password_salt": user_row.password_salt,
        "session_token": user_row.session_token,
    }


def fetch_user_by_username(session, username):
    row = session.query(UserAccount).filter(UserAccount.username == username).one_or_none()
    return {} if row is None else build_user_dictionary(row)


def fetch_user_by_session_token(session, session_token):
    # Signed-out accounts hold empty text, so an empty token must never be looked up.
    if not session_token:
        return {}
    row = session.query(UserAccount).filter(UserAccount.session_token == session_token).one_or_none()
    return {} if row is None else build_user_dictionary(row)


def update_user_session_token(session, username, session_token):
    row = _single_row(session, UserAccount, UserAccount.username, username)
    row.session_token = session_token
    session.commit()
    return username


# ---------------------------------------------------------------- chat turns

def insert_chat_turn(session, chat_record):
    row = _save(session, ChatTurnRecord(**{name: chat_record[name] for name in CHAT_FIELDS}))
    return row.id


def build_chat_turn_dictionary(chat_row):
    record = {name: getattr(chat_row, name) for name in CHAT_FIELDS}
    record["asked_at"] = chat_row.asked_at
    return record


def fetch_recent_chat_turns(session, turn_limit):
    rows = (
        session.query(ChatTurnRecord)
        .order_by(ChatTurnRecord.asked_at.desc(), ChatTurnRecord.id.desc())
        .limit(turn_limit)
        .all()
    )
    return [build_chat_turn_dictionary(row) for row in rows]
