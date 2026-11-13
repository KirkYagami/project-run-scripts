from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Float,
    Boolean,
    DateTime,
    JSON,
    ForeignKey,
    func,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class UserAccount(Base):
    __tablename__ = "user_accounts"
    username = Column(String, primary_key=True)
    display_name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    password_salt = Column(String, nullable=False)
    session_token = Column(String, unique=True, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class AgentRun(Base):
    __tablename__ = "agent_runs"
    run_id = Column(String, primary_key=True)
    thread_id = Column(String, unique=True, nullable=False)
    request_reference = Column(String, nullable=False)
    coordinator_request = Column(Text, nullable=False)
    coordinator_id = Column(String, nullable=False)
    status = Column(String, nullable=False)
    llm_call_count = Column(Integer, nullable=False, default=0)
    started_at = Column(DateTime, server_default=func.now(), nullable=False)
    finished_at = Column(DateTime, nullable=True)


class AuthorisationReview(Base):
    __tablename__ = "authorisation_reviews"
    review_id = Column(String, primary_key=True)
    run_id = Column(
        String, ForeignKey("agent_runs.run_id"), unique=True, nullable=False
    )
    request_reference = Column(String, unique=True, nullable=False)
    service_code = Column(String, nullable=False)
    service_name = Column(String, nullable=False)
    urgency = Column(String, nullable=True)
    policy_document = Column(String, nullable=False)
    body_mass_index = Column(Float, nullable=True)
    criteria = Column(JSON, nullable=False)
    criteria_met_count = Column(Integer, nullable=False)
    criteria_not_met_count = Column(Integer, nullable=False)
    criteria_not_documented_count = Column(Integer, nullable=False)
    screening = Column(String, nullable=False)
    decisions_open = Column(JSON, nullable=False)
    evidence = Column(JSON, nullable=False)
    disagreements = Column(JSON, nullable=False)
    approval_likelihood = Column(Float, nullable=False)
    approval_band = Column(String, nullable=False)
    expected_stay_days = Column(Float, nullable=True)
    requested_inpatient_days = Column(Integer, nullable=True)
    longer_stay_expected = Column(Boolean, nullable=True)
    stay_text = Column(Text, nullable=False)
    coordinator_request = Column(Text, nullable=False)
    review_plan_text = Column(Text, nullable=False)
    criteria_analysis_text = Column(Text, nullable=False)
    evidence_review_text = Column(Text, nullable=False)
    prediction_analysis_text = Column(Text, nullable=False)
    recommendation_text = Column(Text, nullable=False)
    recommended_decision = Column(String, nullable=False)
    status = Column(String, nullable=False)
    letter_text = Column(Text, nullable=True)
    letter_details = Column(JSON, nullable=True)
    notice_text = Column(Text, nullable=True)
    referral_summary = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    status_changed_at = Column(DateTime, server_default=func.now(), nullable=False)


class ReviewDecision(Base):
    __tablename__ = "review_decisions"
    decision_id = Column(Integer, primary_key=True, autoincrement=True)
    review_id = Column(
        String,
        ForeignKey("authorisation_reviews.review_id"),
        unique=True,
        nullable=False,
    )
    run_id = Column(String, ForeignKey("agent_runs.run_id"), nullable=False)
    decision = Column(String, nullable=False)
    decided_by = Column(String, nullable=False)
    decided_by_role = Column(String, nullable=False)
    decision_reason = Column(Text, nullable=False)
    decided_at = Column(DateTime, server_default=func.now(), nullable=False)


class LlmCall(Base):
    __tablename__ = "llm_calls"
    call_id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, ForeignKey("agent_runs.run_id"), nullable=False)
    agent_name = Column(String, nullable=False)
    model_name = Column(String, nullable=False)
    prompt_characters = Column(Integer, nullable=False)
    response_characters = Column(Integer, nullable=False)
    latency_milliseconds = Column(Integer, nullable=False)
    called_at = Column(DateTime, server_default=func.now(), nullable=False)


class ChatTurn(Base):
    __tablename__ = "chat_turns"
    turn_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False)
    user_role = Column(String, nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String, nullable=False)
    request_reference = Column(String, nullable=True)
    answer_text = Column(Text, nullable=False)
    source_documents = Column(Text, nullable=False)
    closest_distance = Column(Float, nullable=True)
    was_refused = Column(Boolean, nullable=False)
    asked_at = Column(DateTime, server_default=func.now(), nullable=False)
