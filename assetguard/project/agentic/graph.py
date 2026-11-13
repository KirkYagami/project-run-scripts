"""Wires the nine steps into one workflow that saves itself to disk after every step."""

import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command

from agentic import nodes
from agentic.state import RepairAdvisoryState
from config import config

STEP_ORDER = [
    ("load_machine_context", nodes.load_machine_context_node),
    ("plan_investigation", nodes.plan_investigation_node),
    ("assess_machine_condition", nodes.assess_machine_condition_node),
    ("identify_problem_type", nodes.identify_problem_type_node),
    ("retrieve_procedure", nodes.retrieve_procedure_node),
    ("compose_repair_job", nodes.compose_repair_job_node),
    ("request_supervisor_review", nodes.request_supervisor_review_node),
    ("finalize_repair_job", nodes.finalize_repair_job_node),
    ("persist_review_outcome", nodes.persist_review_outcome_node),
]


def create_checkpoint_saver(checkpoint_path):
    """An on-disk store for paused runs, usable from the API's worker threads."""
    connection = sqlite3.connect(checkpoint_path, check_same_thread=False)
    return SqliteSaver(connection)


def route_after_review(state):
    """REJECT skips the finalizer; any other decision goes through it."""
    if state["review_decision"]["decision"] == config.REVIEW_DECISION_REJECT:
        return "persist_review_outcome"
    return "finalize_repair_job"


def build_workflow(checkpoint_saver):
    """Register the steps in order, branch after review, and bind the checkpoint store."""
    workflow = StateGraph(RepairAdvisoryState)
    for step_name, step_function in STEP_ORDER:
        workflow.add_node(step_name, step_function)

    workflow.add_edge(START, "load_machine_context")
    linear_steps = [name for name, _ in STEP_ORDER[:7]]
    for current_step, next_step in zip(linear_steps, linear_steps[1:]):
        workflow.add_edge(current_step, next_step)
    # Both destinations are declared on the branch so the drawn graph shows them.
    workflow.add_conditional_edges(
        "request_supervisor_review",
        route_after_review,
        {"finalize_repair_job": "finalize_repair_job", "persist_review_outcome": "persist_review_outcome"},
    )
    workflow.add_edge("finalize_repair_job", "persist_review_outcome")
    workflow.add_edge("persist_review_outcome", END)
    return workflow.compile(checkpointer=checkpoint_saver)


def build_initial_state(advisory_request, thread_id):
    """Every declared key, empty except the request fields and thread_id."""
    return {
        "machine_code": advisory_request["machine_code"],
        "request_text": advisory_request["request_text"],
        "access_level": advisory_request["access_level"],
        "thread_id": thread_id,
        "run_id": "",
        "machine_profile": {},
        "risk_facts": {},
        "problem_facts": {},
        "procedure_facts": {},
        "investigation_plan": {},
        "condition_assessment": {},
        "problem_analysis": {},
        "procedure_guidance": {},
        "draft_repair_job": {},
        "review_decision": {},
        "final_repair_job": {},
        "llm_call_log": [],
    }


def start_advisory_run(compiled_graph, initial_state, thread_config):
    """Run until the review gate pauses the workflow; return the state at the pause."""
    compiled_graph.invoke(initial_state, thread_config, durability="sync")
    return compiled_graph.get_state(thread_config).values


def resume_workflow_after_review(compiled_graph, thread_config, review_decision):
    """Feed the supervisor's answer to the paused gate and run to the end."""
    compiled_graph.invoke(Command(resume=review_decision), thread_config, durability="sync")
    return compiled_graph.get_state(thread_config).values
