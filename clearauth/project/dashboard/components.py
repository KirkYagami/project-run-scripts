import streamlit as st
from config import config as c


def badge(value, colours=None):
    colour = (colours or {}).get(value, c.NEUTRAL_BADGE_COLOUR)
    # Badge contents originate in policy names and staff prose; render as plain text.
    st.badge(str(value), color=colour)


def show_review(record, full=False):
    st.subheader(record["service_name"])
    badge(record["status"], c.STATUS_BADGE_COLOURS)
    st.caption(record["policy_document"])
    badge(record["approval_band"], c.APPROVAL_BAND_BADGE_COLOURS)
    columns = st.columns(4)
    for col, key, label in zip(
        columns,
        c.CRITERIA_COUNT_COLUMNS + ["approval_likelihood"],
        ["Met", "Not met", "Not documented", "Approval likelihood"],
    ):
        col.metric(
            label,
            (
                f"{record[key]:.{c.LIKELIHOOD_DECIMALS}f}"
                if key == "approval_likelihood"
                else record[key]
            ),
        )
    st.write(record["stay_text"])
    st.markdown(record["recommendation_text"])
    badge(record["recommended_decision"], c.DECISION_BADGE_COLOURS)
    for criterion in record["criteria"]:
        st.write(criterion["criterion_name"] + " — " + criterion["result"])
        if criterion["missing_answers"]:
            st.caption(
                "Missing: "
                + ", ".join(
                    c.QUESTIONNAIRE_ANSWER_LABELS[x]
                    for x in criterion["missing_answers"]
                )
            )
    for conflict in record["disagreements"]:
        st.warning(conflict["disagreement_text"])
        st.write(conflict["sentence"])
    for decision in c.DECISIONS:
        if decision not in record["decisions_open"]:
            st.caption(
                decision
                + " is closed: "
                + c.SCREENING_CLOSED_REASONS[record["screening"]]
            )
    if full:
        st.write("Opened by " + record["coordinator_id"])
        st.write(record["coordinator_request"])
        for label, key in [
            ("Review plan", "review_plan_text"),
            ("Criteria analysis", "criteria_analysis_text"),
            ("Evidence review", "evidence_review_text"),
            ("Prediction analysis", "prediction_analysis_text"),
        ]:
            with st.expander(label):
                st.markdown(record[key])
