"""The dispute queue page."""
import pandas as pd
import streamlit as st

from config import config
from dashboard.api_client import call_service


def _badge(label, colours):
    st.badge(str(label), color=colours.get(label, "gray"))


def render_dispute_queue_page():
    """Show the whole open queue in the order the desk should work it."""
    st.header(config.PAGE_QUEUE)
    everything = call_service("GET", "/queue", {"direction": config.QUEUE_DIRECTION_ALL}, None, None)
    direction_counts = {name: sum(1 for row in everything if row["direction"] == name)
                        for name in (config.OVERCHARGED, config.UNDERCHARGED)}
    columns = st.columns(5)
    columns[0].metric("Open disputes", len(everything))
    columns[1].metric(f"Out by GBP {config.REBILL_THRESHOLD_GBP} or more",
                      sum(1 for row in everything if row["rebill_warranted"]))
    columns[2].metric("Overcharged", direction_counts[config.OVERCHARGED])
    columns[3].metric("Undercharged", direction_counts[config.UNDERCHARGED])
    columns[4].metric("Most money at stake",
                      "GBP " + (everything[0]["money_at_stake_gbp"] if everything else "0.00"))

    choice = st.radio("Direction", config.QUEUE_DIRECTION_OPTIONS, horizontal=True)
    rows = call_service("GET", "/queue", {"direction": choice}, None, None)
    st.caption(f"{len(rows)} disputes, most money at stake first.")
    if not rows:
        return
    table = pd.DataFrame([{
        "Reference": row["dispute_reference"], "Centre": row["billing_centre"],
        "Billed tariff": row["billed_tariff"], "Entitled tariff": row["entitled_tariff"],
        "Amount billed": row["amount_billed_gbp"], "Corrected charge": row["corrected_charge_gbp"],
        "Money at stake": row["money_at_stake_gbp"], "Direction": row["direction"],
        "Rebill warranted": row["rebill_warranted"], "Score": row["rebill_probability"],
        "Band": row["rebill_band"]} for row in rows])
    selection = st.dataframe(table, hide_index=True, width="stretch",
                             on_select="rerun", selection_mode="single-row")
    chosen = selection.selection.rows
    if chosen:
        reference = rows[chosen[0]]["dispute_reference"]
        st.session_state["chosen_dispute"] = reference
        st.success(f"{reference} is remembered: open the {config.PAGE_DISPUTE} page to work it.")
