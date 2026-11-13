"""Declares the six tables. Table and column names are exactly as the specification gives them.

Money is held as text written from the exact decimal.Decimal, so no amount passes through a
floating-point number on its way in or out.
"""
import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# The database itself writes every timestamp, to the millisecond.
_NOW = text("(strftime('%Y-%m-%d %H:%M:%f', 'now'))")


class Base(DeclarativeBase):
    """The declarative base every table inherits from."""


class UserAccount(Base):
    __tablename__ = "user_accounts"

    username: Mapped[str] = mapped_column(String, primary_key=True)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    password_salt: Mapped[str] = mapped_column(String, nullable=False)
    session_token: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=_NOW, nullable=False)


class AgentRun(Base):
    __tablename__ = "agent_runs"

    run_id: Mapped[str] = mapped_column(String, primary_key=True)
    thread_id: Mapped[str] = mapped_column(String, nullable=False)
    dispute_reference: Mapped[str] = mapped_column(String, nullable=False)
    analyst_id: Mapped[str] = mapped_column(String, nullable=False)
    analyst_request: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    llm_call_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=_NOW, nullable=False)
    finished_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)


class BillingDispute(Base):
    __tablename__ = "billing_disputes"

    assessment_id: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[str] = mapped_column(String, nullable=False)
    dispute_reference: Mapped[str] = mapped_column(String, nullable=False)
    dispute_id: Mapped[str] = mapped_column(String, nullable=False)
    account_number: Mapped[str] = mapped_column(String, nullable=False)
    billing_centre: Mapped[str] = mapped_column(String, nullable=False)
    analyst_request: Mapped[str] = mapped_column(Text, nullable=False)
    rebill_probability: Mapped[float] = mapped_column(Float, nullable=False)
    rebill_band: Mapped[str] = mapped_column(String, nullable=False)
    dispute_category: Mapped[str] = mapped_column(String, nullable=False)
    cause_agreement: Mapped[float] = mapped_column(Float, nullable=False)
    billed_tariff: Mapped[str] = mapped_column(String, nullable=False)
    entitled_tariff: Mapped[str] = mapped_column(String, nullable=False)
    tariffs_owed: Mapped[str] = mapped_column(Text, nullable=False)
    amount_billed_gbp: Mapped[str] = mapped_column(String, nullable=False)
    corrected_charge_gbp: Mapped[str] = mapped_column(String, nullable=False)
    difference_gbp: Mapped[str] = mapped_column(String, nullable=False)
    direction: Mapped[str] = mapped_column(String, nullable=False)
    rebill_warranted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    breached_standards: Mapped[str] = mapped_column(Text, nullable=False)
    redress_gbp: Mapped[str] = mapped_column(String, nullable=False)
    effort_needed_hours: Mapped[float] = mapped_column(Float, nullable=False)
    senior_review_required: Mapped[bool] = mapped_column(Boolean, nullable=False)
    assessment_plan_text: Mapped[str] = mapped_column(Text, nullable=False)
    assessment_text: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_decision: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    redress_letter_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    rebill_statement_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    settled_amount_gbp: Mapped[str | None] = mapped_column(String, nullable=True)
    settlement_direction: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=_NOW, nullable=False)


class ControllerDecision(Base):
    __tablename__ = "controller_decisions"

    decision_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    assessment_id: Mapped[str] = mapped_column(String, nullable=False)
    run_id: Mapped[str] = mapped_column(String, nullable=False)
    decision: Mapped[str] = mapped_column(String, nullable=False)
    decided_by: Mapped[str] = mapped_column(String, nullable=False)
    decided_by_role: Mapped[str] = mapped_column(String, nullable=False)
    decision_reason: Mapped[str] = mapped_column(Text, nullable=False)
    decided_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=_NOW, nullable=False)


class LlmCall(Base):
    __tablename__ = "llm_calls"

    call_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String, nullable=False)
    agent_name: Mapped[str] = mapped_column(String, nullable=False)
    model_name: Mapped[str] = mapped_column(String, nullable=False)
    prompt_characters: Mapped[int] = mapped_column(Integer, nullable=False)
    response_characters: Mapped[int] = mapped_column(Integer, nullable=False)
    latency_milliseconds: Mapped[int] = mapped_column(Integer, nullable=False)
    called_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=_NOW, nullable=False)


class ChatTurn(Base):
    __tablename__ = "chat_turns"

    turn_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String, nullable=False)
    user_role: Mapped[str] = mapped_column(String, nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(String, nullable=False)
    dispute_reference: Mapped[str | None] = mapped_column(String, nullable=True)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_documents: Mapped[str] = mapped_column(Text, nullable=False)
    closest_distance: Mapped[float] = mapped_column(Float, nullable=False)
    was_refused: Mapped[bool] = mapped_column(Boolean, nullable=False)
    asked_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=_NOW, nullable=False)
