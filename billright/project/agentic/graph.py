"""The order the nodes run in, the gate, the branch and the checkpoint."""
import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph

from agentic import nodes
from agentic.state import DisputeAssessmentState
from config import config


def build_workflow(checkpoint_path):
    """Assemble the ten nodes into a workflow that can be run, paused and resumed."""
    graph = StateGraph(DisputeAssessmentState)
    graph.add_node("load_dispute_context", nodes.load_dispute_context_node)
    graph.add_node("plan_assessment", nodes.plan_assessment_node)
    graph.add_node("assess_rebill_risk", nodes.assess_rebill_risk_node)
    graph.add_node("identify_cause", nodes.identify_cause_node)
    graph.add_node("check_tariff_charges", nodes.check_tariff_charges_node)
    graph.add_node("compose_dispute_assessment", nodes.compose_dispute_assessment_node)
    graph.add_node("request_controller_decision", nodes.request_controller_decision_node)
    graph.add_node("draft_redress_letter", nodes.draft_redress_letter_node)
    graph.add_node("draft_rebill_statement", nodes.draft_rebill_statement_node)
    graph.add_node("record_dispute_outcome", nodes.record_dispute_outcome_node)

    graph.add_edge(START, "load_dispute_context")
    graph.add_edge("load_dispute_context", "plan_assessment")
    graph.add_edge("plan_assessment", "assess_rebill_risk")
    graph.add_edge("assess_rebill_risk", "identify_cause")
    graph.add_edge("identify_cause", "check_tariff_charges")
    graph.add_edge("check_tariff_charges", "compose_dispute_assessment")
    graph.add_edge("compose_dispute_assessment", "request_controller_decision")
    graph.add_conditional_edges("request_controller_decision", nodes.route_controller_decision, {
        config.DECISION_UPHOLD_BILL: "record_dispute_outcome",
        config.DECISION_REBILL: "draft_rebill_statement",
        config.DECISION_REBILL_AND_COMPENSATE: "draft_redress_letter",
    })
    graph.add_edge("draft_redress_letter", "draft_rebill_statement")
    graph.add_edge("draft_rebill_statement", "record_dispute_outcome")
    graph.add_edge("record_dispute_outcome", END)

    connection = sqlite3.connect(checkpoint_path, check_same_thread=False)
    return graph.compile(checkpointer=SqliteSaver(connection))
