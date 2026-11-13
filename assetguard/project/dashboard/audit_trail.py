"""The Audit trail page: what was decided, what the decision changed, and what the run cost.

It reports the record; it never re-judges, re-scores or re-orders it.
"""

from datetime import datetime

import pandas as pd
import streamlit as st

from config import config
from dashboard.manual_chat import CHAT_TYPE_BADGE_COLOURS, NEUTRAL_BADGE_COLOUR
from dashboard.review_queue import numbered_steps_markdown

AUDIT_TABLE_COLUMNS = [
    "repair_job_id", "machine_code", "problem_type", "priority", "estimated_downtime_hours", "status", "created_at",
]
AUDIT_COLUMN_LABELS = {
    "repair_job_id": "Repair job",
    "machine_code": "Machine",
    "problem_type": "Problem type",
    "priority": "Priority",
    "estimated_downtime_hours": "Downtime",
    "status": "Status",
    "created_at": "Created",
}
CALL_AGENT_COLUMN = "agent"
CALL_PROMPT_COLUMN = "prompt characters"
CALL_REPLY_COLUMN = "reply characters"
CALL_SECONDS_COLUMN = "seconds"
CHAT_HEADING_QUESTION_LENGTH = 70


def _to_minute(moment):
    """A stored moment, as text or a datetime, shortened to the date and the minute."""
    if isinstance(moment, str):
        moment = datetime.fromisoformat(moment)
    return moment.strftime("%Y-%m-%d %H:%M")


def render_audit_trail_page(approved_jobs, rejected_jobs):
    st.header(config.PAGE_AUDIT)
    st.caption(
        "Every supervisor decision is kept for seven years under Safety Rule 02 and is open to "
        "internal and statutory audit."
    )
    decided_jobs = approved_jobs + rejected_jobs
    if not decided_jobs:
        st.info("No repair job has been reviewed yet.")
        return

    reviewed_column, approved_column, rejected_column = st.columns(3)
    reviewed_column.metric("Reviewed", len(decided_jobs), border=True)
    approved_column.metric("Approved", len(approved_jobs), border=True)
    rejected_column.metric("Rejected", len(rejected_jobs), border=True)

    register = pd.DataFrame(decided_jobs, columns=AUDIT_TABLE_COLUMNS)
    register["created_at"] = register["created_at"].map(_to_minute)
    st.dataframe(
        register.rename(columns=AUDIT_COLUMN_LABELS),
        hide_index=True,
        width="stretch",
        column_config={
            AUDIT_COLUMN_LABELS["estimated_downtime_hours"]: st.column_config.NumberColumn(format="%.1f h"),
        },
    )


def render_repair_job_text(decided_job):
    st.write(decided_job["job_summary"])
    st.markdown(numbered_steps_markdown(decided_job["task_steps"]))
    st.caption("Sources: " + decided_job["source_documents"])


def render_decision_detail(decided_job, decision_history):
    with st.container(border=True):
        st.markdown("**Decision record**")
        for decision in decision_history:
            with st.container(horizontal=True, width="content", vertical_alignment="center"):
                st.markdown("**" + decision["reviewer_name"] + "**")
                st.badge(decision["decision"],
                         color=config.REVIEW_DECISION_BADGE_COLOURS.get(decision["decision"], "gray"))
                st.caption(_to_minute(decision["decided_at"]))
            if decision["feedback_text"].strip():
                st.markdown("Asked for: " + decision["feedback_text"])
            else:
                st.markdown("Asked for: *nothing in particular*")

        reviewed_draft = decision_history[-1]["reviewed_draft"] if decision_history else ""
        changes_applied = decided_job["changes_applied"].strip()

        if decided_job["status"] == config.REPAIR_JOB_STATUS_REJECTED:
            st.error("Rejected: no repair job was issued.")
            with st.expander("The rejected draft, as the agents wrote it"):
                st.text(reviewed_draft)
        elif not changes_applied or changes_applied.lower() == "none":
            st.warning(
                "Approved without changes: the finalizer made none. An instruction has to say what to "
                "change before the finalizer can act on it."
            )
            with st.expander("The approved repair job"):
                render_repair_job_text(decided_job)
        else:
            st.success("The review changed the repair job: " + changes_applied)
            with st.expander("Compare the reviewed draft with the approved version"):
                st.markdown("**Draft the supervisor reviewed**")
                st.text(reviewed_draft)
                st.divider()
                st.markdown("**Approved version**")
                render_repair_job_text(decided_job)


def build_call_table(call_records):
    """One row per logged call, in the order the calls ran."""
    return pd.DataFrame([
        {
            CALL_AGENT_COLUMN: call["agent_name"],
            CALL_PROMPT_COLUMN: call["prompt_characters"],
            CALL_REPLY_COLUMN: call["response_characters"],
            CALL_SECONDS_COLUMN: round(call["latency_milliseconds"] / 1000, 2),
        }
        for call in call_records
    ], columns=[CALL_AGENT_COLUMN, CALL_PROMPT_COLUMN, CALL_REPLY_COLUMN, CALL_SECONDS_COLUMN])


def render_call_budget(call_budget):
    with st.container(border=True):
        st.markdown("**Language model calls**")
        calls_column, time_column = st.columns(2)
        calls_column.metric(
            "Calls used", str(call_budget["call_count"]) + " of " + str(call_budget["expected_call_count"]),
            help="A rejected repair job skips the finalizer, so it is one call cheaper by design.")
        time_column.metric("Total model time", f"{call_budget['total_latency_milliseconds'] / 1000:.1f} s")
        st.dataframe(
            build_call_table(call_budget["calls"]).rename(columns={
                CALL_AGENT_COLUMN: "Agent",
                CALL_PROMPT_COLUMN: "Prompt characters",
                CALL_REPLY_COLUMN: "Reply characters",
                CALL_SECONDS_COLUMN: "Seconds",
            }),
            hide_index=True,
            width="stretch",
            column_config={"Seconds": st.column_config.NumberColumn(format="%.2f")},
        )


def render_chat_log(chat_turns):
    st.subheader("Manual assistant log")
    if not chat_turns:
        st.info("Nothing has been asked of the manual assistant yet.")
        return

    st.caption("The " + str(len(chat_turns)) + " most recent questions, newest first.")
    for chat_turn in chat_turns:
        heading = (
            _to_minute(chat_turn["asked_at"]) + " · " + chat_turn["username"] + " · "
            + chat_turn["question"][:CHAT_HEADING_QUESTION_LENGTH]
        )
        with st.expander(heading):
            st.badge(chat_turn["question_type"],
                     color=CHAT_TYPE_BADGE_COLOURS.get(chat_turn["question_type"], NEUTRAL_BADGE_COLOUR))
            st.text(chat_turn["answer"])
            if chat_turn["source_documents"]:
                st.caption("Sources: " + chat_turn["source_documents"])
