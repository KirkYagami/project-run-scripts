from typing import TypedDict, Annotated
import operator


class AuthorisationReviewState(TypedDict, total=False):
    request_reference: object
    coordinator_request: object
    coordinator_id: object
    thread_id: object
    run_id: object
    review_id: object
    request_profile: object
    request_documents: object
    screening: object
    evidence_findings: object
    disagreements: object
    likelihood: object
    stay: object
    review_plan: object
    criteria_analysis: object
    evidence_review: object
    prediction_analysis: object
    review_decision: object
    office_letter: object
    letter_details: object
    member_notice: object
    llm_call_count: Annotated[int, operator.add]
