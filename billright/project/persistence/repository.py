"""Every read and write against the six tables.

Nothing outside this module builds a query, so the service, the workflow and the chat all see
the same rows in the same shape: plain records, not database objects. Every function takes an
open session the caller opened from session_factory, and every write is committed before the
function returns.
"""
import datetime

from sqlalchemy import literal_column, select, update

from config import config
from persistence.models import (
    AgentRun,
    BillingDispute,
    ChatTurn,
    ControllerDecision,
    LlmCall,
    UserAccount,
)


def _columns_of(table_class):
    return [column.name for column in table_class.__table__.columns]


def _record(table_class, row):
    return {name: getattr(row, name) for name in _columns_of(table_class)}


def _only_columns(table_class, values):
    names = set(_columns_of(table_class))
    unknown = sorted(set(values) - names)
    if unknown:
        raise ValueError(f"{table_class.__tablename__} has no column named {unknown}.")
    return dict(values)


# ------------------------------------------------------------------ accounts
def insert_user_account(session, account_record):
    """Create one sign-in account."""
    session.add(UserAccount(**_only_columns(UserAccount, account_record)))
    session.commit()
    return account_record["username"]


def fetch_user_account(session, condition):
    """Find one account."""
    row = session.execute(select(UserAccount).where(condition)).scalars().first()
    return None if row is None else _record(UserAccount, row)


def update_session_token(session, username, session_token):
    """Start or end one person's session."""
    session.execute(update(UserAccount).where(UserAccount.username == username)
                    .values(session_token=session_token))
    session.commit()
    return username


# ------------------------------------------------------------------ runs and calls
def insert_agent_run(session, run_record):
    """Record that an assessment has started."""
    values = _only_columns(AgentRun, run_record)
    values.setdefault("llm_call_count", 0)
    session.add(AgentRun(**values))
    session.commit()
    return values["run_id"]


def update_agent_run(session, run_id, status_value, llm_call_count):
    """Move a run through its life: waiting, complete or failed."""
    values = {"status": status_value, "llm_call_count": llm_call_count}
    if status_value in config.AGENT_RUN_FINISHED_STATUSES:
        values["finished_at"] = datetime.datetime.now()
    session.execute(update(AgentRun).where(AgentRun.run_id == run_id).values(**values))
    session.commit()
    return run_id


def insert_llm_call(session, run_id, call_record):
    """Record what one language model call cost."""
    values = {key: call_record[key] for key in ("agent_name", "model_name", "prompt_characters",
                                                "response_characters", "latency_milliseconds")}
    row = LlmCall(run_id=run_id, **values)
    session.add(row)
    session.commit()
    return int(row.call_id)


def fetch_llm_calls(session, run_id):
    """Read back every call a run made, in the order the calls were made."""
    rows = session.execute(select(LlmCall).where(LlmCall.run_id == run_id)
                           .order_by(LlmCall.call_id)).scalars().all()
    return [_record(LlmCall, row) for row in rows]


# ------------------------------------------------------------------ assessments
def insert_billing_dispute(session, dispute_record):
    """Record the assessment the Revenue Controller will decide."""
    session.add(BillingDispute(**_only_columns(BillingDispute, dispute_record)))
    session.commit()
    return dispute_record["assessment_id"]


def record_dispute_outcome(session, assessment_id, outcome_record):
    """Write what the decision led to onto the assessment."""
    values = _only_columns(BillingDispute, outcome_record)
    if session.get(BillingDispute, assessment_id) is None:
        raise ValueError(f"No assessment carries the identifier {assessment_id}.")
    if values:
        session.execute(update(BillingDispute).where(BillingDispute.assessment_id == assessment_id)
                        .values(**values))
        session.commit()
    return assessment_id


def fetch_dispute_records(session, condition):
    """Read assessments with everything known about them, newest first."""
    rows = session.execute(
        select(BillingDispute, AgentRun)
        .join(AgentRun, AgentRun.run_id == BillingDispute.run_id, isouter=True)
        .where(condition)
        .order_by(BillingDispute.created_at.desc(), literal_column("billing_disputes.rowid").desc())
    ).all()
    records = []
    for dispute, run in rows:
        record = _record(BillingDispute, dispute)
        record["thread_id"] = None if run is None else run.thread_id
        record["analyst_id"] = None if run is None else run.analyst_id
        record["llm_call_count"] = None if run is None else run.llm_call_count
        decisions = session.execute(
            select(ControllerDecision).where(ControllerDecision.assessment_id == dispute.assessment_id)
            .order_by(ControllerDecision.decision_id.desc())).scalars().first()
        for name in ("decision", "decided_by", "decided_by_role", "decision_reason", "decided_at"):
            record[name] = None if decisions is None else getattr(decisions, name)
        records.append(record)
    return records


def insert_controller_decision(session, decision_record):
    """Record who decided what, and why."""
    row = ControllerDecision(**_only_columns(ControllerDecision, decision_record))
    session.add(row)
    session.commit()
    return int(row.decision_id)


# ------------------------------------------------------------------ chat
def insert_chat_turn(session, turn_record):
    """Keep every question the chat was asked."""
    row = ChatTurn(**_only_columns(ChatTurn, turn_record))
    session.add(row)
    session.commit()
    return int(row.turn_id)


def fetch_chat_turns(session, condition, turn_limit):
    """Read back recent chat turns, newest first."""
    rows = session.execute(select(ChatTurn).where(condition)
                           .order_by(ChatTurn.turn_id.desc()).limit(turn_limit)).scalars().all()
    return [_record(ChatTurn, row) for row in rows]
