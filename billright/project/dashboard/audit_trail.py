"""The audit trail page: assessed disputes, the record behind each, the call budget and the chat log."""
import pandas as pd
import streamlit as st

from config import config
from dashboard.api_client import call_service


def render_audit_trail_page():
    """Show what has been assessed and decided, and every question the chat has been asked."""
    st.header(config.PAGE_AUDIT)
    disputes_tab, chat_tab = st.tabs(["Assessed disputes", "Chat log"])
    with disputes_tab:
        statuses = st.multiselect("Statuses", config.DISPUTE_STATUS_OPTIONS,
                                  default=config.DECIDED_DISPUTE_STATUSES)
        if not statuses:
            st.info("Choose at least one status.")
        else:
            records = call_service("GET", "/disputes", {"status_value": statuses}, None, None)
            counts = st.columns(len(statuses))
            for column, status in zip(counts, statuses):
                column.metric(status, sum(1 for record in records if record["status"] == status))
            if records:
                labels = {f"{r['dispute_reference']} ({r['assessment_id']})": r for r in records}
                record = labels[st.selectbox("Assessment", list(labels))]
                st.write(f"Status {record['status']}; recommendation {record['recommended_decision']}; "
                         f"opened by {record['analyst_id']} at {record['created_at']}")
                if record["decision"]:
                    st.write(f"Decision {record['decision']} by {record['decided_by']} "
                             f"({record['decided_by_role']}) at {record['decided_at']}: {record['decision_reason']}")
                    if record["settled_amount_gbp"] is not None:
                        st.write(f"Settled amount GBP {record['settled_amount_gbp']} "
                                 f"({record['settlement_direction']})")
                st.subheader("Assessment"); st.write(record["assessment_text"])
                if record["redress_letter_text"]:
                    st.subheader("Redress letter"); st.text(record["redress_letter_text"])
                if record["rebill_statement_text"]:
                    st.subheader("Corrected bill statement"); st.text(record["rebill_statement_text"])
                budget = call_service("GET", f"/disputes/{record['assessment_id']}/calls", None, None, None)
                st.subheader("Call budget")
                st.write(f"{budget['call_count']} calls made against {budget['expected_call_count']} expected; "
                         f"total latency {budget['total_latency_milliseconds']} ms")
                if budget["calls"]:
                    st.dataframe(pd.DataFrame(budget["calls"]), hide_index=True, width="stretch")
    with chat_tab:
        turns = call_service("GET", "/audit/chat-turns", {"turn_limit": config.CHAT_AUDIT_MAX_ROWS}, None, None)
        if turns:
            st.dataframe(pd.DataFrame([{
                "When": turn["asked_at"], "Who": turn["username"], "Role": turn["user_role"],
                "Question": turn["question_text"], "Type": turn["question_type"],
                "Dispute": turn["dispute_reference"], "Refused": turn["was_refused"],
                "Sources": turn["source_documents"]} for turn in turns]),
                hide_index=True, width="stretch")
        else:
            st.info("No question has been asked yet.")
