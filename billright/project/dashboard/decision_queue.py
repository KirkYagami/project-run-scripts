"""The decision queue page and the decision form."""
import streamlit as st

from config import config
from dashboard.api_client import call_service


def render_decision_queue_page():
    """Show the assessments waiting at the gate and let a Revenue Controller decide one."""
    st.header(config.PAGE_DECISION)
    waiting = call_service("GET", "/disputes", {"status_value": [config.DISPUTE_STATUS_PENDING]}, None, None)
    if not waiting:
        st.info("No assessment is waiting for a decision.")
        return
    labels = {f"{item['dispute_reference']} ({item['assessment_id']})": item for item in waiting}
    chosen = labels[st.selectbox("Assessment", list(labels))]
    st.metric("Recommendation", chosen["recommended_decision"])
    columns = st.columns(4)
    columns[0].metric("Direction", chosen["direction"])
    columns[1].metric("Score", f"{chosen['rebill_probability']} ({chosen['rebill_band']})")
    columns[2].metric("Category", chosen["dispute_category"])
    columns[3].metric("Effort", f"{chosen['effort_needed_hours']} hours")
    money = st.columns(4)
    money[0].metric("Amount billed", f"GBP {chosen['amount_billed_gbp']}")
    money[1].metric("Corrected charge", f"GBP {chosen['corrected_charge_gbp']}")
    money[2].metric("Difference", f"GBP {chosen['difference_gbp']}")
    money[3].metric("Compensation due", f"GBP {chosen['redress_gbp']}")
    st.subheader("Assessment"); st.write(chosen["assessment_text"])
    st.write(f"Opened by {chosen['analyst_id']}, who asked: {chosen['analyst_request']}")
    with st.expander("The plan"):
        st.text(chosen["assessment_plan_text"])

    if chosen["analyst_id"] == st.session_state.get("username"):
        st.warning(config.OWN_ASSESSMENT_REFUSED_MESSAGE)
        return
    st.subheader("Decide")
    decision = st.radio("Decision", config.DECISION_OPTIONS,
                        captions=[f"{config.LLM_CALLS_BY_DECISION[option] - config.LLM_CALLS_BEFORE_DECISION} "
                                  f"further model call(s)" for option in config.DECISION_OPTIONS])
    reason = st.text_area("Reason", key=f"reason_{chosen['assessment_id']}")
    ready = len(reason.strip()) >= config.DECISION_REASON_MINIMUM_CHARACTERS
    if st.button("Record the decision", disabled=not ready):
        result = call_service("POST", f"/disputes/{chosen['assessment_id']}/decision", None,
                              {"decision": decision, "decision_reason": reason},
                              "Recording the decision and writing what it calls for")
        message = f"The dispute reached {result['status']}."
        if result["settled_amount_gbp"] is not None:
            message += f" Settled amount GBP {result['settled_amount_gbp']} ({result['settlement_direction']})."
        st.success(message)
