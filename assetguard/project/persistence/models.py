"""Every table the application database holds. Column names are a data contract."""

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, func

from persistence.database import Base


class AgentRun(Base):
    """One row per execution of the advisory workflow."""

    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, unique=True, nullable=False, index=True)
    thread_id = Column(String, nullable=False)
    machine_code = Column(String, nullable=False)
    request_text = Column(Text, nullable=False)
    status = Column(String, nullable=False)
    started_at = Column(DateTime, server_default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)


class RepairJobDraft(Base):
    """One row per repair job the agents drafted, updated in place after review."""

    __tablename__ = "repair_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    repair_job_id = Column(String, unique=True, nullable=False, index=True)
    run_id = Column(String, nullable=False, index=True)
    machine_code = Column(String, nullable=False)
    machine_type = Column(String, nullable=False)
    breakdown_probability = Column(Float, nullable=False)
    risk_band = Column(String, nullable=False)
    problem_type = Column(String, nullable=False)
    priority = Column(String, nullable=False)
    estimated_downtime_hours = Column(Float, nullable=False)
    permit_required = Column(Text, nullable=False)
    procedure_reference = Column(Text, nullable=False)
    parts_required = Column(Text, nullable=False)
    task_steps = Column(Text, nullable=False)
    safety_notes = Column(Text, nullable=False)
    proposed_window = Column(String, nullable=False)
    source_documents = Column(Text, nullable=False)
    job_summary = Column(Text, nullable=False)
    scheduling_note = Column(Text, nullable=False)
    changes_applied = Column(Text, nullable=False, default="")
    status = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class ReviewDecision(Base):
    """One row per supervisor decision on a drafted repair job."""

    __tablename__ = "review_decisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, nullable=False, index=True)
    repair_job_id = Column(String, nullable=False)
    decision = Column(String, nullable=False)
    reviewer_name = Column(String, nullable=False)
    feedback_text = Column(Text, nullable=False)
    reviewed_draft = Column(Text, nullable=False)
    decided_at = Column(DateTime, server_default=func.now(), nullable=False)


class LlmCallRecord(Base):
    """One row per language model call an agent made during a run."""

    __tablename__ = "llm_calls"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, nullable=False, index=True)
    agent_name = Column(String, nullable=False)
    model_name = Column(String, nullable=False)
    prompt_characters = Column(Integer, nullable=False)
    response_characters = Column(Integer, nullable=False)
    latency_milliseconds = Column(Integer, nullable=False)
    called_at = Column(DateTime, server_default=func.now(), nullable=False)


class UserAccount(Base):
    """One row per person who may sign in. No password is ever stored, only its hash and salt."""

    __tablename__ = "user_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False, index=True)
    display_name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    password_salt = Column(String, nullable=False)
    session_token = Column(String, nullable=False, default="", index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class ChatTurnRecord(Base):
    """One row per question put to the manual assistant, and what it answered."""

    __tablename__ = "chat_turns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False)
    question = Column(Text, nullable=False)
    question_type = Column(String, nullable=False)
    answer = Column(Text, nullable=False)
    source_documents = Column(Text, nullable=False)
    machine_code = Column(String, nullable=False)
    latency_milliseconds = Column(Integer, nullable=False)
    asked_at = Column(DateTime, server_default=func.now(), nullable=False)
