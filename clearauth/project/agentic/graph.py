import sqlite3
from pathlib import Path
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from .state import AuthorisationReviewState
from . import nodes
from config import config as c


def build_workflow(checkpoint_path):
    Path(checkpoint_path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(checkpoint_path, check_same_thread=False)
    saver = SqliteSaver(connection)
    graph = StateGraph(AuthorisationReviewState)
    order = [
        "load_request_context",
        "plan_review",
        "assess_criteria",
        "review_evidence",
        "weigh_predictions",
        "compose_review_recommendation",
        "request_review_decision",
    ]
    for name in order + [
        "draft_office_letter",
        "draft_member_notice",
        "record_review_outcome",
    ]:
        graph.add_node(name, getattr(nodes, name + "_node"))
    graph.add_edge(START, order[0])
    for a, b in zip(order, order[1:]):
        graph.add_edge(a, b)
    graph.add_conditional_edges(
        "request_review_decision",
        nodes.route_review_decision,
        {
            c.DECISION_APPROVE: "draft_office_letter",
            c.DECISION_REQUEST_INFORMATION: "draft_office_letter",
            c.DECISION_REFER: "record_review_outcome",
        },
    )
    graph.add_conditional_edges(
        "draft_office_letter",
        nodes.route_review_decision,
        {
            c.DECISION_APPROVE: "draft_member_notice",
            c.DECISION_REQUEST_INFORMATION: "record_review_outcome",
        },
    )
    graph.add_edge("draft_member_notice", "record_review_outcome")
    graph.add_edge("record_review_outcome", END)
    return graph.compile(checkpointer=saver)
