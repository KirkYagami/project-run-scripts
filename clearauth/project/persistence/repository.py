from sqlalchemy import select, func
from .models import (
    UserAccount,
    AgentRun,
    AuthorisationReview,
    ReviewDecision,
    LlmCall,
    ChatTurn,
)


def _record(row):
    return {col.name: getattr(row, col.name) for col in row.__table__.columns}


def _insert(session, model, record):
    session.add(model(**record))
    session.flush()


def insert_user_account(session, account_record):
    _insert(session, UserAccount, account_record)


def fetch_user_account(session, condition):
    row = session.scalars(select(UserAccount).where(condition)).first()
    return _record(row) if row else None


def update_session_token(session, username, session_token):
    row = session.get(UserAccount, username)
    if row is None:
        raise ValueError(f"Unknown user {username}")
    row.session_token = session_token
    session.flush()


def insert_agent_run(session, run_record):
    _insert(session, AgentRun, run_record)


def update_agent_run(session, run_id, status_value, llm_call_count):
    row = session.get(AgentRun, run_id)
    if row is None:
        raise ValueError(f"Unknown run {run_id}")
    row.status = status_value
    row.llm_call_count = llm_call_count
    if (
        status_value
        in __import__(
            "config.config", fromlist=["AGENT_RUN_FINISHED_STATUSES"]
        ).AGENT_RUN_FINISHED_STATUSES
    ):
        row.finished_at = func.now()
    session.flush()


def insert_llm_call(session, run_id, call_record):
    _insert(session, LlmCall, dict(call_record, run_id=run_id))


def fetch_llm_calls(session, run_id):
    return [
        {
            k: getattr(r, k)
            for k in [
                "agent_name",
                "model_name",
                "prompt_characters",
                "response_characters",
                "latency_milliseconds",
            ]
        }
        for r in session.scalars(
            select(LlmCall).where(LlmCall.run_id == run_id).order_by(LlmCall.call_id)
        )
    ]


def insert_authorisation_review(session, review_record):
    _insert(session, AuthorisationReview, review_record)


def fetch_review_records(session, condition):
    rows = session.execute(
        select(AuthorisationReview, AgentRun, ReviewDecision)
        .join(AgentRun, AuthorisationReview.run_id == AgentRun.run_id)
        .outerjoin(
            ReviewDecision, AuthorisationReview.review_id == ReviewDecision.review_id
        )
        .where(condition)
        .order_by(
            AuthorisationReview.created_at.desc(), AuthorisationReview.review_id.desc()
        )
    ).all()
    return [
        _record(r)
        | dict(
            thread_id=run.thread_id,
            coordinator_id=run.coordinator_id,
            llm_call_count=run.llm_call_count,
        )
        | {
            k: getattr(d, k) if d else None
            for k in ["decision", "decided_by", "decided_by_role", "decision_reason"]
        }
        for r, run, d in rows
    ]


def insert_review_decision(session, decision_record):
    _insert(session, ReviewDecision, decision_record)


def record_review_outcome(session, review_id, outcome_record):
    row = session.get(AuthorisationReview, review_id)
    if row is None:
        raise ValueError(f"Unknown review {review_id}")
    for k, v in outcome_record.items():
        setattr(row, k, v)
    row.status_changed_at = func.now()
    session.flush()


def insert_chat_turn(session, turn_record):
    _insert(session, ChatTurn, turn_record)


def fetch_chat_turns(session, condition, turn_limit):
    return [
        _record(row)
        for row in session.scalars(
            select(ChatTurn)
            .where(condition)
            .order_by(ChatTurn.turn_id.desc())
            .limit(turn_limit)
        )
    ]
