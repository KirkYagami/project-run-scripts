import pandas as pd
import streamlit as st
from config import config as c
from .api_client import call_service
from .components import show_review


def render_audit_trail_page():
    st.title(c.PAGE_AUDIT)
    reviews_tab, chat_tab = st.tabs(["Review records", "Chat audit"])
    with reviews_tab:
        statuses = st.multiselect(
            "Statuses", c.REVIEW_STATUS_OPTIONS, default=c.DECIDED_REVIEW_STATUSES
        )
        reviews = (
            call_service("GET", "/reviews", query={"status_value": statuses})
            if statuses
            else []
        )
        if not reviews:
            st.info("No matching reviews.")
        else:
            st.dataframe(
                pd.DataFrame(reviews)[
                    [
                        "request_reference",
                        "service_name",
                        "status",
                        "coordinator_id",
                        "decision",
                        "decided_by",
                        "llm_call_count",
                    ]
                ],
                hide_index=True,
                width="stretch",
            )
            r = st.selectbox(
                "Inspect review",
                reviews,
                format_func=lambda v: v["review_id"] + " · " + v["request_reference"],
            )
            show_review(r, full=True)
            if r["decision"]:
                st.write(
                    dict(
                        decision=r["decision"],
                        decided_by=r["decided_by"],
                        role=r["decided_by_role"],
                        reason=r["decision_reason"],
                    )
                )
            for title, key in [
                (c.LETTER_KINDS.get(r["decision"], "Provider letter"), "letter_text"),
                ("Member notice", "notice_text"),
                ("Referral summary", "referral_summary"),
            ]:
                if r.get(key):
                    st.subheader(title)
                    st.write(r[key])
            if r.get("letter_details"):
                st.json(r["letter_details"])
            budget = call_service("GET", "/reviews/" + r["review_id"] + "/calls")
            st.metric(
                "Model calls",
                f"{budget['call_count']} / {budget['expected_call_count']}",
            )
            st.caption(
                f"Total latency: {budget['total_latency_milliseconds']/1000:.{c.LATENCY_SECONDS_DECIMALS}f} seconds"
            )
            st.dataframe(budget["calls"], hide_index=True)
    with chat_tab:
        turns = call_service(
            "GET", "/audit/chat-turns", query={"turn_limit": c.CHAT_AUDIT_MAX_ROWS}
        )
        st.dataframe(turns, hide_index=True, width="stretch")
