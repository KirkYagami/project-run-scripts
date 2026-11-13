"""The ten steps of the workflow, and the router out of the gate.

Each node takes the state, does one thing, and returns only the keys it wrote. Every node that
calls an agent records the call against the run as soon as the agent function returns it.
"""
import secrets

import pandas as pd
from langgraph.types import interrupt

from agentic import agents
from config import config
from data_pipeline.dataset_loader import load_raw_dataset
from knowledge.tariff_reading import read_standard_payments, read_tariff_schedule
from knowledge.vector_index import open_vector_index
from modeling.model_registry import load_feature_schema, load_model
from persistence import repository
from persistence.database import session_factory
from tools.charge_tools import (
    build_charge_pieces,
    compare_with_billed,
    compute_corrected_charge,
    compute_redress,
    compute_settled_amount,
    measure_usage,
)
from tools.dispute_data_tools import fetch_dispute_notes, fetch_dispute_profile
from tools.prediction_tools import build_cause_facts, build_rebill_facts, estimate_resolution_effort
from tools.retrieval_tools import read_customer_steps

# ------------------------------------------------------------------ resources, opened once
rebill_model = load_model(config.REBILL_MODEL_FILE)
effort_model = load_model(config.EFFORT_MODEL_FILE)
cause_model = load_model(config.CAUSE_MODEL_FILE)
rebill_feature_names = load_feature_schema(config.REBILL_SCHEMA_FILE)
effort_feature_names = load_feature_schema(config.EFFORT_SCHEMA_FILE)
open_disputes = load_raw_dataset(config.OPEN_DISPUTES_FILE, config.NULL_TOKENS)
open_dispute_notes = load_raw_dataset(config.OPEN_DISPUTE_NOTES_FILE, config.NULL_TOKENS)
knowledge_collection = open_vector_index(config.VECTOR_STORE_DIRECTORY, config.VECTOR_COLLECTION_NAME)
tariff_schedules = {tariff: read_tariff_schedule(knowledge_collection, tariff)
                    for tariff in config.TARIFF_DOCUMENT_BY_TARIFF}
standard_payments = read_standard_payments(knowledge_collection)


# ------------------------------------------------------------------ helpers
def _new_identifier(prefix):
    return prefix + secrets.token_hex(config.IDENTIFIER_HEX_LENGTH)[:config.IDENTIFIER_HEX_LENGTH].upper()


def _record_call(run_id, call_record):
    session = session_factory()
    try:
        repository.insert_llm_call(session, run_id, call_record)
    finally:
        session.close()


def _labelled(fields):
    return "\n".join(f"{label}: {text}" for label, text in fields.items())


# ------------------------------------------------------------------ the nodes
def load_dispute_context_node(state):
    """Gather everything about the dispute that needs no language model, and open the run."""
    reference = state["dispute_reference"]
    profile = fetch_dispute_profile(open_disputes, reference)
    notes = fetch_dispute_notes(open_dispute_notes, reference)
    rebill_facts = build_rebill_facts(rebill_model, rebill_feature_names, pd.DataFrame([profile]))[0]
    cause_facts = build_cause_facts(cause_model, notes)
    run_id = _new_identifier(config.RUN_ID_PREFIX)
    assessment_id = _new_identifier(config.ASSESSMENT_ID_PREFIX)
    session = session_factory()
    try:
        repository.insert_agent_run(session, {
            "run_id": run_id, "thread_id": state["thread_id"], "dispute_reference": reference,
            "analyst_id": state["analyst_id"], "analyst_request": state["analyst_request"],
            "status": config.AGENT_RUN_STATUS_RUNNING, "llm_call_count": 0})
    finally:
        session.close()
    return {"run_id": run_id, "assessment_id": assessment_id, "dispute_profile": profile,
            "rebill_facts": rebill_facts, "cause_facts": cause_facts}


def plan_assessment_node(state):
    """Ask the planning agent what has to be established."""
    result = agents.plan_assessment(state["dispute_profile"], state["analyst_request"])
    _record_call(state["run_id"], result["call_record"])
    return {"assessment_plan": result["assessment_plan"], "llm_call_log": [result["call_record"]]}


def assess_rebill_risk_node(state):
    """Ask the rebill agent to explain the score."""
    result = agents.assess_rebill_risk(state["rebill_facts"], state["dispute_profile"],
                                       state["assessment_plan"])
    _record_call(state["run_id"], result["call_record"])
    return {"rebill_assessment": result["rebill_assessment"], "llm_call_log": [result["call_record"]]}


def identify_cause_node(state):
    """Ask the cause agent how much weight the notes deserve."""
    result = agents.identify_cause(state["cause_facts"], state["dispute_profile"],
                                   state["assessment_plan"], state["rebill_assessment"])
    _record_call(state["run_id"], result["call_record"])
    return {"cause_analysis": result["cause_analysis"], "llm_call_log": [result["call_record"]]}


def check_tariff_charges_node(state):
    """Have the corrected bill rebuilt by the charge tools and stated by the tariff agent."""
    profile = state["dispute_profile"]
    usage = measure_usage(profile)
    pieces = build_charge_pieces(profile, tariff_schedules)
    corrected = compute_corrected_charge(pieces, usage)
    comparison = compare_with_billed(profile, corrected["corrected_charge_gbp"])
    redress = compute_redress(profile, standard_payments)
    tariffs = []
    for piece in corrected["pieces"]:
        if piece["tariff"] not in tariffs:
            tariffs.append(piece["tariff"])
    billed = profile[config.BILLED_TARIFF_COLUMN]
    if billed not in tariffs:
        tariffs.append(billed)
    charge_facts = {"tariff_schedules": {tariff: tariff_schedules[tariff] for tariff in tariffs},
                    "usage": usage, "pieces": corrected["pieces"], "comparison": comparison,
                    "redress": redress}
    result = agents.advise_on_tariff_charges(charge_facts, profile, state["assessment_plan"])
    _record_call(state["run_id"], result["call_record"])
    return {"charge_facts": charge_facts, "tariff_advice": result["tariff_advice"],
            "llm_call_log": [result["call_record"]]}


def compose_dispute_assessment_node(state):
    """Give the Revenue Controller a stored assessment to decide from."""
    profile, charge_facts = state["dispute_profile"], state["charge_facts"]
    comparison, redress = charge_facts["comparison"], charge_facts["redress"]
    effort_facts = estimate_resolution_effort(
        effort_model, effort_feature_names, profile, state["rebill_facts"]["rebill_band"],
        state["cause_facts"]["dispute_category"], charge_facts["pieces"], comparison["money_at_stake_gbp"])
    result = agents.write_dispute_assessment(
        profile, state["analyst_request"], state["rebill_facts"], charge_facts, effort_facts,
        state["rebill_assessment"], state["cause_analysis"], state["tariff_advice"])
    _record_call(state["run_id"], result["call_record"])
    tariffs_owed = []
    for piece in charge_facts["pieces"]:
        if piece["tariff"] not in tariffs_owed:
            tariffs_owed.append(piece["tariff"])
    written = result["dispute_assessment"]
    session = session_factory()
    try:
        repository.insert_billing_dispute(session, {
            "assessment_id": state["assessment_id"], "run_id": state["run_id"],
            "dispute_reference": state["dispute_reference"], "dispute_id": profile["dispute_id"],
            "account_number": profile["account_number"], "billing_centre": profile["billing_centre"],
            "analyst_request": state["analyst_request"],
            "rebill_probability": state["rebill_facts"]["rebill_probability"],
            "rebill_band": state["rebill_facts"]["rebill_band"],
            "dispute_category": state["cause_facts"]["dispute_category"],
            "cause_agreement": state["cause_facts"]["agreement"],
            "billed_tariff": profile[config.BILLED_TARIFF_COLUMN],
            "entitled_tariff": profile[config.ENTITLED_TARIFF_COLUMN],
            "tariffs_owed": ", ".join(tariffs_owed),
            "amount_billed_gbp": str(comparison["amount_billed_gbp"]),
            "corrected_charge_gbp": str(comparison["corrected_charge_gbp"]),
            "difference_gbp": str(comparison["difference_gbp"]),
            "direction": comparison["direction"], "rebill_warranted": comparison["rebill_warranted"],
            "breached_standards": ", ".join(item["standard_code"] for item in redress["breached_standards"]),
            "redress_gbp": str(redress["redress_gbp"]),
            "effort_needed_hours": effort_facts["effort_needed_hours"],
            "senior_review_required": effort_facts["senior_review_required"],
            "assessment_plan_text": _labelled(state["assessment_plan"]),
            "assessment_text": written["ASSESSMENT"],
            "recommended_decision": written["RECOMMENDED DECISION"],
            "status": config.DISPUTE_STATUS_PENDING})
    finally:
        session.close()
    return {"llm_call_log": [result["call_record"]]}


def request_controller_decision_node(state):
    """Hold the run until a Revenue Controller decides, and take in that decision."""
    session = session_factory()
    try:
        repository.update_agent_run(session, state["run_id"], config.AGENT_RUN_STATUS_AWAITING_DECISION,
                                    len(state.get("llm_call_log") or []))
    finally:
        session.close()
    decision = interrupt({"assessment_id": state["assessment_id"], "run_id": state["run_id"]})
    comparison = state["charge_facts"]["comparison"]
    settlement = compute_settled_amount(decision["decision"], comparison["difference_gbp"],
                                        state["charge_facts"]["redress"]["redress_gbp"])
    return {"controller_decision": decision, "redress_letter": {}, "rebill_statement": {},
            "settlement": settlement}


def route_controller_decision(state):
    """Choose the path out of the gate, from the decision and nothing else."""
    return state["controller_decision"]["decision"]


def draft_redress_letter_node(state):
    """Have the redress letter written."""
    steps = read_customer_steps(knowledge_collection, state["cause_facts"]["dispute_category"])
    result = agents.draft_redress_letter(state["dispute_profile"], state["charge_facts"]["redress"], steps)
    _record_call(state["run_id"], result["call_record"])
    return {"redress_letter": result["redress_letter"], "llm_call_log": [result["call_record"]]}


def draft_rebill_statement_node(state):
    """Have the corrected bill statement written."""
    result = agents.draft_rebill_statement(state["dispute_profile"], state["charge_facts"],
                                           state.get("redress_letter") or {}, state.get("settlement"))
    _record_call(state["run_id"], result["call_record"])
    return {"rebill_statement": result["rebill_statement"], "llm_call_log": [result["call_record"]]}


def record_dispute_outcome_node(state):
    """Write the decision and everything it led to, and close the run."""
    decision = state["controller_decision"]
    settlement = state.get("settlement")
    letter, statement = state.get("redress_letter") or {}, state.get("rebill_statement") or {}
    session = session_factory()
    try:
        repository.insert_controller_decision(session, {
            "assessment_id": state["assessment_id"], "run_id": state["run_id"],
            "decision": decision["decision"], "decided_by": decision["decided_by"],
            "decided_by_role": decision["decided_by_role"], "decision_reason": decision["decision_reason"]})
        repository.record_dispute_outcome(session, state["assessment_id"], {
            "status": config.DISPUTE_STATUS_BY_DECISION[decision["decision"]],
            "redress_letter_text": _labelled(letter) if letter else None,
            "rebill_statement_text": _labelled(statement) if statement else None,
            "settled_amount_gbp": str(settlement["settled_amount_gbp"]) if settlement else None,
            "settlement_direction": settlement["direction"] if settlement else None})
        repository.update_agent_run(session, state["run_id"], config.AGENT_RUN_STATUS_COMPLETE,
                                    len(state.get("llm_call_log") or []))
    finally:
        session.close()
    return {}
