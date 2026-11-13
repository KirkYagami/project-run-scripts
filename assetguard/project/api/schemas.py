"""The shapes of everything that enters and leaves the service.

Field names are a contract read by the dashboard. A request that fails these
checks is refused with 422 before any workflow step or model call runs.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from config import config


class AdvisoryRequest(BaseModel):
    machine_code: str = Field(min_length=3)
    request_text: str = Field(min_length=5)
    access_level: str

    @field_validator("access_level")
    @classmethod
    def access_level_is_known(cls, value):
        if value not in config.ACCESS_LEVEL_OPTIONS:
            raise ValueError("access_level must be one of " + str(config.ACCESS_LEVEL_OPTIONS))
        return value


class ReviewDecisionRequest(BaseModel):
    decision: str
    reviewer_name: str = Field(min_length=2)
    feedback_text: str

    @field_validator("decision")
    @classmethod
    def decision_is_known(cls, value):
        if value not in config.REVIEW_DECISION_OPTIONS:
            raise ValueError("decision must be one of " + str(config.REVIEW_DECISION_OPTIONS))
        return value


class MachineProfileResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    machine_code: str
    machine_type: str
    factory_name: str
    production_line: str
    importance: str
    usage_pattern: str
    machine_age_months: float
    average_vibration: float
    average_temperature_c: float
    oil_dirtiness_score: float
    alarms_this_week: float
    days_since_last_service: float
    breakdowns_last_year: float


class RiskAssessmentResponse(BaseModel):
    machine_code: str
    breakdown_probability: float
    risk_band: str
    priority: str
    importance: str


class RepairJobResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    repair_job_id: str
    run_id: str
    machine_code: str
    machine_type: str
    breakdown_probability: float
    risk_band: str
    problem_type: str
    priority: str
    estimated_downtime_hours: float
    permit_required: str
    procedure_reference: str
    parts_required: str
    task_steps: str
    safety_notes: str
    proposed_window: str
    source_documents: str
    job_summary: str
    scheduling_note: str
    changes_applied: str
    status: str
    created_at: str

    @field_validator("status")
    @classmethod
    def status_is_known(cls, value):
        if value not in config.REPAIR_JOB_STATUS_OPTIONS:
            raise ValueError("status must be one of " + str(config.REPAIR_JOB_STATUS_OPTIONS))
        return value


class ReviewDecisionResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    run_id: str
    repair_job_id: str
    decision: str
    reviewer_name: str
    feedback_text: str
    reviewed_draft: str
    decided_at: str

    @field_validator("decision")
    @classmethod
    def decision_is_known(cls, value):
        if value not in config.REVIEW_DECISION_OPTIONS:
            raise ValueError("decision must be one of " + str(config.REVIEW_DECISION_OPTIONS))
        return value


class FleetRiskRow(BaseModel):
    model_config = ConfigDict(extra="ignore")

    machine_code: str
    machine_type: str
    factory_name: str
    importance: str
    breakdown_probability: float
    risk_band: str
    priority: str
    average_vibration: float
    average_temperature_c: float
    alarms_this_week: float


class MachineNoteHistoryResponse(BaseModel):
    machine_code: str
    note_count: int
    detected_problem_type: str
    confidence: float
    problem_votes: dict[str, int]
    recent_notes: list[str]


class CallBudgetResponse(BaseModel):
    run_id: str
    call_count: int
    expected_call_count: int
    total_latency_milliseconds: int
    calls: list[dict]


class SignInRequest(BaseModel):
    username: str = Field(min_length=3)
    password: str = Field(min_length=1)


class SignedInUserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    username: str
    display_name: str
    role: str
    session_token: str
    allowed_pages: list[str]


class SignOutResponse(BaseModel):
    signed_out: bool


class ChatTurn(BaseModel):
    question: str
    answer: str


class ChatRequest(BaseModel):
    question: str = Field(min_length=2)
    history: list[ChatTurn]


class ChatResponse(BaseModel):
    question_type: str
    answer: str
    source_documents: list[str]
    chunks_searched: int


class ChatTurnResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    username: str
    question: str
    question_type: str
    answer: str
    source_documents: str
    machine_code: str
    latency_milliseconds: int
    asked_at: datetime
