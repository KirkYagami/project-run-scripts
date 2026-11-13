"""The Fleet overview page: which machines are closest to failing, and how many sit in each band.

Every figure here is one the service already worked out.
"""

import pandas as pd
import streamlit as st

from config import config

FLEET_TABLE_COLUMNS = [
    "machine_code", "machine_type", "factory_name", "importance", "risk_band", "priority", "breakdown_probability",
]
FLEET_COLUMN_LABELS = {
    "machine_code": "Machine",
    "machine_type": "Type",
    "factory_name": "Factory",
    "importance": "Importance",
    "risk_band": "Risk band",
    "priority": "Priority",
    "breakdown_probability": "Breakdown probability",
}
BAND_CHOICE_ALL = "ALL"


def count_machines_by_band(fleet_rows):
    """Machines per band, read from the band the service assigned; every band present."""
    counts = {config.RISK_BAND_HIGH: 0, config.RISK_BAND_MEDIUM: 0, config.RISK_BAND_LOW: 0}
    for row in fleet_rows:
        if row["risk_band"] in counts:
            counts[row["risk_band"]] += 1
    return counts


def build_fleet_table(fleet_rows, chosen_band):
    """The display columns for the chosen band, in the order the service supplied."""
    selected = [row for row in fleet_rows if chosen_band == BAND_CHOICE_ALL or row["risk_band"] == chosen_band]
    return pd.DataFrame(selected, columns=FLEET_TABLE_COLUMNS)


def render_fleet_overview_page(fleet_rows):
    st.header(config.PAGE_FLEET)
    st.caption(
        "Each machine's chance of a breakdown in the next 30 days, from the breakdown risk model. "
        "HIGH is " + str(config.HIGH_RISK_THRESHOLD) + " or more, MEDIUM is "
        + str(config.MEDIUM_RISK_THRESHOLD) + " or more, LOW is everything below (Policy 01)."
    )
    if not fleet_rows:
        st.info("No machines were returned. The AssetGuard AI service may not be running.")
        return

    counts = count_machines_by_band(fleet_rows)
    total_column, high_column, medium_column, low_column = st.columns(4)
    total_column.metric("Machines monitored", len(fleet_rows), border=True)
    high_column.metric(
        "High risk", counts[config.RISK_BAND_HIGH], border=True,
        help="Plan a repair job now: open the machine on Machine detail and raise an advisory run.")
    medium_column.metric(
        "Medium risk", counts[config.RISK_BAND_MEDIUM], border=True,
        help="Watch closely and bring forward at the next planned service window.")
    low_column.metric("Low risk", counts[config.RISK_BAND_LOW], border=True)

    chosen_band = st.segmented_control(
        "Risk band",
        [BAND_CHOICE_ALL, config.RISK_BAND_HIGH, config.RISK_BAND_MEDIUM, config.RISK_BAND_LOW],
        default=BAND_CHOICE_ALL,
    ) or BAND_CHOICE_ALL

    fleet_table = build_fleet_table(fleet_rows, chosen_band)
    st.dataframe(
        fleet_table.rename(columns=FLEET_COLUMN_LABELS),
        hide_index=True,
        width="stretch",
        column_config={
            FLEET_COLUMN_LABELS["breakdown_probability"]: st.column_config.NumberColumn(format="%.3f"),
        },
    )
    st.caption(
        str(len(fleet_table)) + " machines shown, most at risk first. Open one on the "
        + config.PAGE_MACHINE + " page to see its notes and raise a repair job."
    )
