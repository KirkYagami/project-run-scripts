from typing import Literal, Annotated, Any
from datetime import datetime
from pydantic import BaseModel, StringConstraints, create_model
from config import config as c

ServiceFilter = Literal[tuple(c.QUEUE_SERVICE_OPTIONS)]
ReviewStatusValue = Literal[tuple(c.REVIEW_STATUS_OPTIONS)]
DecisionValue = Literal[tuple(c.DECISIONS)]
CoordinatorRequestText = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=c.COORDINATOR_REQUEST_MINIMUM_CHARACTERS,
        max_length=c.COORDINATOR_REQUEST_MAXIMUM_CHARACTERS,
    ),
]
DecisionReasonText = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=c.DECISION_REASON_MINIMUM_CHARACTERS,
        max_length=c.DECISION_REASON_MAXIMUM_CHARACTERS,
    ),
]
QuestionText = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=c.CHAT_QUESTION_MINIMUM_CHARACTERS,
        max_length=c.CHAT_QUESTION_MAXIMUM_CHARACTERS,
    ),
]


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


class ReviewRequest(BaseModel):
    request_reference: str
    coordinator_request: CoordinatorRequestText


class DecisionRequest(BaseModel):
    decision: DecisionValue
    decision_reason: DecisionReasonText


class ChatRequest(BaseModel):
    question: QuestionText


class QueueRow(BaseModel):
    queue_position: int
    request_reference: str
    service_code: str
    service_name: str
    urgency: str
    site_of_service: str
    document_count: int
    criteria_met_count: int
    criteria_not_met_count: int
    criteria_not_documented_count: int
    screening: str
    decisions_open: list[str]
    approval_likelihood: float
    approval_band: str
    disagreement_count: int


class RequestDetailResponse(BaseModel):
    queue_position: int
    request: dict
    request_documents: list[dict]
    screening: dict
    evidence_findings: list[dict]
    disagreements: list[dict]
    likelihood: dict
    stay: dict
    stay_text: str


class CallBudgetResponse(BaseModel):
    review_id: str
    run_id: str
    call_count: int
    expected_call_count: int
    total_latency_milliseconds: int
    calls: list[dict]


class ChatResponse(BaseModel):
    question_type: str
    request_reference: str | None
    answer: str
    source_documents: list[str]
    closest_distance: float | None
    was_refused: bool


# Keep database and response fields aligned. JSON columns contain plain tool outputs.
from persistence.models import AuthorisationReview, ChatTurn
from sqlalchemy import String, Text, Integer, Float, Boolean, JSON, DateTime

_types = {
    String: str,
    Text: str,
    Integer: int,
    Float: float,
    Boolean: bool,
    JSON: Any,
    DateTime: datetime,
}


def _fields(model):
    out = {}
    for col in model.__table__.columns:
        typ = next(v for k, v in _types.items() if isinstance(col.type, k))
        out[col.name] = (typ | None if col.nullable else typ, ...)
    return out


ReviewRecordResponse = create_model(
    "ReviewRecordResponse",
    **_fields(AuthorisationReview),
    thread_id=(str, ...),
    coordinator_id=(str, ...),
    llm_call_count=(int, ...),
    decision=(str | None, ...),
    decided_by=(str | None, ...),
    decided_by_role=(str | None, ...),
    decision_reason=(str | None, ...)
)
ChatTurnResponse = create_model("ChatTurnResponse", **_fields(ChatTurn))
