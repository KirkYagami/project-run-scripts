"""The shape of every request the service accepts and every reply it returns.

A request that does not meet the stated conditions is refused with status 422 before any work
is done. Every amount of money is a decimal.Decimal, so it travels as exact text.
"""
import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from config import config

DirectionFilter = Literal[tuple(config.QUEUE_DIRECTION_OPTIONS)]
DisputeStatusValue = Literal[tuple(config.DISPUTE_STATUS_OPTIONS)]
DecisionValue = Literal[tuple(config.DECISION_OPTIONS)]
ChatQuestionType = Literal[tuple(config.CHAT_TYPE_OPTIONS)]


class SignInRequest(BaseModel):
    username: str
    password: str


class SignedInUserResponse(BaseModel):
    username: str
    display_name: str
    role: str
    session_token: str
    pages: list[str]
    areas: list[str]


class SignedOutResponse(BaseModel):
    username: str
    signed_out: bool


class QueueRow(BaseModel):
    dispute_reference: str
    billing_centre: str
    billed_tariff: str
    entitled_tariff: str
    amount_billed_gbp: Decimal
    corrected_charge_gbp: Decimal
    difference_gbp: Decimal
    money_at_stake_gbp: Decimal
    direction: str
    rebill_warranted: bool
    rebill_probability: float
    rebill_band: str


class DisputeDetailResponse(BaseModel):
    profile: dict
    note_texts: list[str]
    rebill: dict
    cause: dict
    charge: dict
    effort: dict


class AssessmentRequest(BaseModel):
    dispute_reference: str
    analyst_request: str = Field(min_length=config.ANALYST_REQUEST_MINIMUM_CHARACTERS)


class DecisionRequest(BaseModel):
    decision: DecisionValue
    decision_reason: str = Field(min_length=config.DECISION_REASON_MINIMUM_CHARACTERS)


class BillingDisputeResponse(BaseModel):
    assessment_id: str
    run_id: str
    thread_id: str
    analyst_id: str
    dispute_reference: str
    dispute_id: str
    account_number: str
    billing_centre: str
    analyst_request: str
    rebill_probability: float
    rebill_band: str
    dispute_category: str
    cause_agreement: float
    billed_tariff: str
    entitled_tariff: str
    tariffs_owed: str
    amount_billed_gbp: Decimal
    corrected_charge_gbp: Decimal
    difference_gbp: Decimal
    direction: str
    rebill_warranted: bool
    breached_standards: str
    redress_gbp: Decimal
    effort_needed_hours: float
    senior_review_required: bool
    assessment_plan_text: str
    assessment_text: str
    recommended_decision: str
    status: DisputeStatusValue
    redress_letter_text: str | None
    rebill_statement_text: str | None
    settled_amount_gbp: Decimal | None
    settlement_direction: str | None
    created_at: datetime.datetime
    llm_call_count: int
    decision: str | None
    decided_by: str | None
    decided_by_role: str | None
    decision_reason: str | None
    decided_at: datetime.datetime | None


class CallBudgetResponse(BaseModel):
    assessment_id: str
    run_id: str
    call_count: int
    expected_call_count: int
    total_latency_milliseconds: int
    calls: list[dict]


class ChatRequest(BaseModel):
    question: str = Field(min_length=config.CHAT_QUESTION_MINIMUM_CHARACTERS)


class ChatResponse(BaseModel):
    question_type: ChatQuestionType
    dispute_reference: str | None
    answer: str
    source_documents: list[str]
    was_refused: bool


class ChatTurnResponse(BaseModel):
    turn_id: int
    username: str
    user_role: str
    question_text: str
    question_type: str
    dispute_reference: str | None
    answer_text: str
    source_documents: str
    closest_distance: float
    was_refused: bool
    asked_at: datetime.datetime
