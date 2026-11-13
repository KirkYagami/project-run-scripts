import pandas as pd
import streamlit as st
from config import config as c
from .api_client import call_service


def render_review_queue_page():
    st.title(c.PAGE_QUEUE)
    st.caption(
        "Urgent requests first. Every result is established by the review service."
    )
    whole = call_service("GET", "/queue", query={"service_code": c.QUEUE_SERVICE_ALL})
    cols = st.columns(5)
    metrics = [
        ("Requests", len(whole)),
        ("Urgent", sum(r["urgency"] == c.URGENT for r in whole)),
        ("All criteria met", sum(r["screening"] == c.DECISION_APPROVE for r in whole)),
        ("Answers missing", sum(r["criteria_not_documented_count"] > 0 for r in whole)),
        ("Criteria not met", sum(r["criteria_not_met_count"] > 0 for r in whole)),
    ]
    for col, (label, value) in zip(cols, metrics):
        col.metric(label, value)
    service = st.selectbox(
        "Service",
        c.QUEUE_SERVICE_OPTIONS,
        format_func=lambda x: c.QUEUE_SERVICE_LABELS[x],
    )
    rows = (
        whole
        if service == c.QUEUE_SERVICE_ALL
        else call_service("GET", "/queue", query={"service_code": service})
    )
    if not rows:
        st.info("No requests for this service.")
        return
    event = st.dataframe(
        pd.DataFrame(rows).drop(columns=["decisions_open"]),
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        width="stretch",
        column_config={
            "approval_likelihood": st.column_config.NumberColumn(
                "Likelihood", format="%.4f"
            )
        },
    )
    if event.selection.rows:
        ref = rows[event.selection.rows[0]]["request_reference"]
        st.session_state["selected_request"] = ref
        st.success("Selected " + ref + ". Open Request detail to review it.")
