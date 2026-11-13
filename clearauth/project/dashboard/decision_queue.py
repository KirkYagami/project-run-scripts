import streamlit as st
from config import config as c
from .api_client import call_service
from .components import show_review


def render_decision_queue_page():
    st.title(c.PAGE_DECISION)
    reviews = call_service(
        "GET", "/reviews", query={"status_value": [c.REVIEW_STATUS_AWAITING]}
    )
    if not reviews:
        st.info("No reviews are waiting for a decision.")
        return
    review = st.selectbox(
        "Review",
        reviews,
        format_func=lambda r: f"{r['request_reference']} · {r['service_name']} · {r['urgency']}",
    )
    show_review(review, full=True)
    if (
        review["coordinator_id"].strip().lower()
        == st.session_state["user"]["username"].strip().lower()
    ):
        st.info("Another UM Nurse Reviewer must decide this review.")
        return
    with st.form("decide_" + review["review_id"]):
        decision = st.selectbox("Decision", review["decisions_open"])
        reason = st.text_area(
            "Your reason", max_chars=c.DECISION_REASON_MAXIMUM_CHARACTERS
        )
        submit = st.form_submit_button("Record decision", type="primary")
    if submit:
        if len(reason.strip()) < c.DECISION_REASON_MINIMUM_CHARACTERS:
            st.error(
                "Please give a reason of at least "
                + str(c.DECISION_REASON_MINIMUM_CHARACTERS)
                + " characters."
            )
            return
        result = call_service(
            "POST",
            "/reviews/" + review["review_id"] + "/decision",
            payload=dict(decision=decision, decision_reason=reason.strip()),
            waiting_message="Recording the decision and preparing its correspondence",
        )
        st.success(result["status"] + ": " + c.DECISION_OUTCOME_TEXTS[decision])
        show_review(result)
