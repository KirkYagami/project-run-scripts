"""The single state dictionary every workflow step reads and writes.

This is also exactly what is written to disk at the review pause, so it defines
what a resumed run remembers.
"""

import operator
from typing import Annotated, TypedDict


class RepairAdvisoryState(TypedDict):
    machine_code: str
    request_text: str
    access_level: str
    thread_id: str
    run_id: str
    machine_profile: dict
    risk_facts: dict
    problem_facts: dict
    procedure_facts: dict
    investigation_plan: dict
    condition_assessment: dict
    problem_analysis: dict
    procedure_guidance: dict
    draft_repair_job: dict
    review_decision: dict
    final_repair_job: dict
    # Each step returns a one-entry list; operator.add appends it to the log
    # instead of replacing the log.
    llm_call_log: Annotated[list, operator.add]
