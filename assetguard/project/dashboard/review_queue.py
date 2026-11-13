"""The Review queue page: where a supervisor approves, modifies or rejects a drafted repair job.

Until a decision is submitted here the advisory run stays paused on disk and
nothing is issued. The page decides nothing; it carries the answer unchanged.
"""

import streamlit as st

from config import config


def numbered_steps_markdown(task_steps):
    """Stored steps, one per line, as a numbered list whose numbers are made here."""
    steps = [step.strip() for step in task_steps.splitlines() if step.strip()]
    return "\n".join(str(number) + ". " + step for number, step in enumerate(steps, start=1))


def render_repair_job_summary(repair_job):
    with st.container(horizontal=True, width="content"):
        st.badge(repair_job["risk_band"] + " risk",
                 color=config.RISK_BAND_BADGE_COLOURS.get(repair_job["risk_band"], "gray"))
        st.badge("Priority " + repair_job["priority"], color="blue")
        st.badge(repair_job["problem_type"], color="violet")
    st.caption(repair_job["machine_code"] + " · " + repair_job["machine_type"])
    st.write(repair_job["job_summary"])

    card_column, steps_column = st.columns(2)
    with card_column, st.container(border=True):
        st.markdown("**Job card**")
        st.markdown("**Procedure:** " + repair_job["procedure_reference"])
        st.markdown("**Parts:** " + repair_job["parts_required"])
        st.markdown("**Estimated downtime:** " + str(repair_job["estimated_downtime_hours"]) + " hours")
        st.markdown("**Proposed window:** " + repair_job["proposed_window"])
        st.caption(repair_job["scheduling_note"])
    with steps_column, st.container(border=True):
        st.markdown("**Task steps**")
        st.markdown(numbered_steps_markdown(repair_job["task_steps"]))
        st.caption("Sources: " + repair_job["source_documents"])

    st.warning(
        "**Permit required:** " + repair_job["permit_required"] + "\n\n**Safety notes:** " + repair_job["safety_notes"],
        icon="⚠️",
    )


def render_decision_form(repair_job, decision_handler):
    repair_job_id = repair_job["repair_job_id"]
    with st.form(key="decision-" + repair_job_id):
        decision_column, name_column = st.columns(2)
        decision = decision_column.radio(
            "Decision", config.REVIEW_DECISION_OPTIONS, horizontal=True, key="decision-choice-" + repair_job_id)
        reviewer_name = name_column.text_input("Your name", key="reviewer-" + repair_job_id)
        feedback_text = st.text_area(
            "Instruction to the finalizer",
            placeholder="e.g. Add replacing the coupling element to step 3 and book the Saturday night window.",
            key="feedback-" + repair_job_id,
        )
        st.caption(
            "Approving or modifying costs one further language model call, because the finalizer "
            "rewrites the repair job. Rejecting costs none."
        )
        submitted = st.form_submit_button("Submit decision", type="primary")

    if not submitted:
        return
    if len(reviewer_name.strip()) < 2:
        st.error("Enter your name (at least two characters) before submitting a decision.")
        return
    with st.spinner("Recording the decision and letting the paused run finish..."):
        decision_handler(repair_job_id, {
            "decision": decision,
            "reviewer_name": reviewer_name.strip(),
            "feedback_text": feedback_text,
        })
    st.rerun()


def render_review_queue_page(pending_repair_jobs, decision_handler):
    st.header(config.PAGE_REVIEW)
    if not pending_repair_jobs:
        st.info(
            "Nothing is waiting for a decision. Raise an advisory run from the "
            + config.PAGE_MACHINE + " page and its draft will appear here."
        )
        return

    st.caption(
        str(len(pending_repair_jobs)) + " repair jobs drafted and unactioned. Under Safety Rule 02 no machine "
        "leaves service without an approved shutdown authorisation."
    )
    for repair_job in pending_repair_jobs:
        label = repair_job["repair_job_id"] + " · " + repair_job["machine_code"] + " · " + repair_job["priority"]
        with st.expander(label, expanded=len(pending_repair_jobs) == 1):
            render_repair_job_summary(repair_job)
            render_decision_form(repair_job, decision_handler)
