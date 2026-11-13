"""The nine steps of the advisory run.

Each step reads the shared state, does one piece of work, and returns only the
keys it changed. Tool work happens here, in plain code; agents only interpret.
Everything slow to load is loaded once, when this module is imported.
"""

import uuid

from langgraph.types import interrupt

from agentic.agents import (
    condition_analyst_agent,
    problem_analyst_agent,
    procedure_advisor_agent,
    repair_job_finalizer_agent,
    repair_job_writer_agent,
    work_planner_agent,
)
from config import config
from data_pipeline.dataset_loader import load_processed_dataset
from modeling.model_registry import load_feature_schema, load_model_artifact
from persistence.database import open_database_session
from persistence.repository import (
    apply_review_outcome,
    insert_agent_run,
    insert_llm_call_record,
    insert_repair_job_draft,
    insert_review_decision,
    update_agent_run_status,
    update_repair_job_status,
)
from tools.machine_data_tools import fetch_machine_note_history, fetch_machine_profile, load_current_fleet
from tools.prediction_tools import (
    apply_tight_space_factor,
    build_model_input_row,
    build_planned_repair_record,
    classify_risk_band,
    detect_problem_type,
    estimate_repair_downtime,
    predict_breakdown_probability,
    resolve_repair_priority,
)
from tools.retrieval_tools import lookup_repair_procedure, lookup_safety_requirement, open_manual_search

BREAKDOWN_MODEL = load_model_artifact(config.BREAKDOWN_MODEL_FILE)
BREAKDOWN_SCHEMA = load_feature_schema(config.BREAKDOWN_SCHEMA_FILE)
DOWNTIME_MODEL = load_model_artifact(config.DOWNTIME_MODEL_FILE)
DOWNTIME_SCHEMA = load_feature_schema(config.DOWNTIME_SCHEMA_FILE)
PROBLEM_TYPE_MODEL = load_model_artifact(config.PROBLEM_TYPE_MODEL_FILE)
TEXT_VECTORIZER = load_model_artifact(config.TEXT_VECTORIZER_FILE)
CURRENT_FLEET = load_current_fleet(config.CURRENT_FLEET_FILE)
TECHNICIAN_NOTES = load_processed_dataset(config.CLEAN_TECHNICIAN_NOTES_FILE)
MANUAL_SEARCH = open_manual_search(config.VECTOR_STORE_DIRECTORY, config.VECTOR_COLLECTION_NAME)

RISK_THRESHOLDS = {"high": config.HIGH_RISK_THRESHOLD, "medium": config.MEDIUM_RISK_THRESHOLD}


def _record_call(run_id, call_record):
    """Write one spent call to the database straight away, in its own session."""
    session = open_database_session()
    try:
        insert_llm_call_record(session, call_record, run_id)
    finally:
        session.close()


def _agent_output(agent_result):
    """The agent's fields without the call measurement, which goes to the log instead."""
    return {name: value for name, value in agent_result.items() if name != "call_record"}


def load_machine_context_node(state):
    machine_profile = fetch_machine_profile(CURRENT_FLEET, state["machine_code"])
    if not machine_profile:
        raise LookupError("Machine " + state["machine_code"] + " is not in the current fleet")

    run_id = "RUN-" + uuid.uuid4().hex[:12].upper()
    session = open_database_session()
    try:
        insert_agent_run(session, {
            "run_id": run_id,
            "thread_id": state["thread_id"],
            "machine_code": state["machine_code"],
            "request_text": state["request_text"],
            "status": config.AGENT_RUN_STATUS_RUNNING,
        })
    finally:
        session.close()
    return {"run_id": run_id, "machine_profile": machine_profile}


def plan_investigation_node(state):
    result = work_planner_agent(state["machine_profile"], state["request_text"])
    _record_call(state["run_id"], result["call_record"])
    return {"investigation_plan": _agent_output(result), "llm_call_log": [result["call_record"]]}


def assess_machine_condition_node(state):
    machine_profile = state["machine_profile"]
    feature_row = build_model_input_row(machine_profile, BREAKDOWN_SCHEMA)
    probability = predict_breakdown_probability(BREAKDOWN_MODEL, feature_row)
    risk_band = classify_risk_band(probability, RISK_THRESHOLDS)
    risk_facts = {
        "breakdown_probability": probability,
        "risk_band": risk_band,
        "priority": resolve_repair_priority(machine_profile["importance"], risk_band),
    }

    result = condition_analyst_agent(machine_profile, risk_facts, state["investigation_plan"])
    _record_call(state["run_id"], result["call_record"])
    return {
        "risk_facts": risk_facts,
        "condition_assessment": _agent_output(result),
        "llm_call_log": [result["call_record"]],
    }


def identify_problem_type_node(state):
    note_history = fetch_machine_note_history(TECHNICIAN_NOTES, state["machine_code"])
    problem_facts = detect_problem_type(PROBLEM_TYPE_MODEL, TEXT_VECTORIZER, note_history)

    result = problem_analyst_agent(problem_facts, state["condition_assessment"])
    _record_call(state["run_id"], result["call_record"])
    return {
        "problem_facts": problem_facts,
        "problem_analysis": _agent_output(result),
        "llm_call_log": [result["call_record"]],
    }


def retrieve_procedure_node(state):
    machine_type = state["machine_profile"]["machine_type"]
    procedure = lookup_repair_procedure(MANUAL_SEARCH, machine_type, state["problem_facts"]["problem_type"])
    safety = lookup_safety_requirement(MANUAL_SEARCH, machine_type)

    source_documents = []
    for document_name in procedure["source_documents"] + safety["source_documents"]:
        if document_name not in source_documents:
            source_documents.append(document_name)
    procedure_facts = {
        "procedure_context": procedure["context_text"],
        "safety_context": safety["context_text"],
        "source_documents": source_documents,
    }

    result = procedure_advisor_agent(procedure_facts, state["problem_analysis"])
    _record_call(state["run_id"], result["call_record"])
    return {
        "procedure_facts": procedure_facts,
        "procedure_guidance": _agent_output(result),
        "llm_call_log": [result["call_record"]],
    }


def compose_repair_job_node(state):
    risk_facts = state["risk_facts"]
    problem_type = state["problem_facts"]["problem_type"]
    guidance = state["procedure_guidance"]

    # The downtime model is asked to assume the baseline access level; the
    # Safety Rule 03 tight space stretch is then applied once, by the rule.
    planned_record = build_planned_repair_record(
        state["machine_profile"], risk_facts,
        {"problem_type": problem_type, "access_level": config.ACCESS_LEVEL_BASELINE},
    )
    model_hours = estimate_repair_downtime(DOWNTIME_MODEL, build_model_input_row(planned_record, DOWNTIME_SCHEMA))
    estimated_downtime_hours = apply_tight_space_factor(model_hours, state["access_level"])

    result = repair_job_writer_agent(state["condition_assessment"], state["problem_analysis"], guidance)
    _record_call(state["run_id"], result["call_record"])

    draft_repair_job = {
        "repair_job_id": "WO-" + uuid.uuid4().hex[:10].upper(),
        "run_id": state["run_id"],
        "machine_code": state["machine_code"],
        "machine_type": state["machine_profile"]["machine_type"],
        "breakdown_probability": risk_facts["breakdown_probability"],
        "risk_band": risk_facts["risk_band"],
        "problem_type": problem_type,
        "priority": risk_facts["priority"],
        "estimated_downtime_hours": estimated_downtime_hours,
        "permit_required": guidance.get("permit_required", ""),
        "procedure_reference": guidance.get("procedure_reference", ""),
        "parts_required": guidance.get("parts_required", ""),
        "task_steps": "\n".join(result["task_steps"]),
        "safety_notes": guidance.get("safety_notes", ""),
        "proposed_window": config.STANDARD_SHUTDOWN_WINDOW,
        "source_documents": ", ".join(state["procedure_facts"]["source_documents"]),
        "job_summary": result.get("job_summary", ""),
        "scheduling_note": result.get("scheduling_note", ""),
        "status": config.REPAIR_JOB_STATUS_PENDING,
    }

    session = open_database_session()
    try:
        insert_repair_job_draft(session, draft_repair_job)
        update_agent_run_status(session, state["run_id"], config.AGENT_RUN_STATUS_AWAITING_REVIEW)
    finally:
        session.close()
    return {"draft_repair_job": draft_repair_job, "llm_call_log": [result["call_record"]]}


def request_supervisor_review_node(state):
    """The human gate. interrupt() saves the run to disk and stops until a supervisor answers."""
    draft = state["draft_repair_job"]
    review_summary = {name: draft[name] for name in (
        "repair_job_id", "machine_code", "risk_band", "priority",
        "estimated_downtime_hours", "job_summary", "task_steps", "proposed_window")}
    review_summary["decision_options"] = config.REVIEW_DECISION_OPTIONS
    review_decision = interrupt(review_summary)
    return {"review_decision": dict(review_decision)}


def finalize_repair_job_node(state):
    draft = state["draft_repair_job"]
    result = repair_job_finalizer_agent(draft, state["review_decision"])
    _record_call(state["run_id"], result["call_record"])

    final_repair_job = dict(draft)
    # If the model's reply could not be read, keep the draft wording rather than
    # wiping it: nothing the supervisor did not ask to change may be dropped.
    final_repair_job["job_summary"] = result.get("final_summary") or draft["job_summary"]
    final_repair_job["task_steps"] = "\n".join(result["task_steps"]) if result["task_steps"] else draft["task_steps"]
    final_repair_job["changes_applied"] = result.get("changes_applied") or "No changes"
    final_repair_job["status"] = config.REPAIR_JOB_STATUS_APPROVED
    return {"final_repair_job": final_repair_job, "llm_call_log": [result["call_record"]]}


def persist_review_outcome_node(state):
    draft = state["draft_repair_job"]
    decision = state["review_decision"]
    session = open_database_session()
    try:
        insert_review_decision(session, {
            "run_id": state["run_id"],
            "repair_job_id": draft["repair_job_id"],
            "decision": decision["decision"],
            "reviewer_name": decision["reviewer_name"],
            "feedback_text": decision["feedback_text"],
            # What the supervisor actually saw, kept before the finalizer's version replaces it.
            "reviewed_draft": "JOB SUMMARY:\n" + draft["job_summary"] + "\n\nTASK STEPS:\n" + draft["task_steps"],
        })
        if decision["decision"] == config.REVIEW_DECISION_REJECT:
            update_repair_job_status(session, draft["repair_job_id"], config.REPAIR_JOB_STATUS_REJECTED)
        else:
            apply_review_outcome(session, draft["repair_job_id"], state["final_repair_job"])
        update_agent_run_status(session, state["run_id"], config.AGENT_RUN_STATUS_COMPLETE)
    finally:
        session.close()
    return {}
