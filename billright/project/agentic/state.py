"""What the workflow carries from one node to the next."""
import operator
from typing import Annotated, TypedDict


class DisputeAssessmentState(TypedDict, total=False):
    """Every key the nodes read or write, and nothing else.

    llm_call_log accumulates across nodes; every other key is replaced by whichever node
    writes it.
    """
    dispute_reference: str
    analyst_request: str
    analyst_id: str
    thread_id: str
    run_id: str
    assessment_id: str
    dispute_profile: dict
    rebill_facts: dict
    cause_facts: dict
    charge_facts: dict
    assessment_plan: dict
    rebill_assessment: dict
    cause_analysis: dict
    tariff_advice: dict
    controller_decision: dict
    redress_letter: dict
    rebill_statement: dict
    settlement: dict | None
    llm_call_log: Annotated[list[dict], operator.add]
