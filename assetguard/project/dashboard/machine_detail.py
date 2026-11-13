"""The Machine detail page: everything known about one machine, on one screen.

It draws the combined record from fetch_machine_detail and asks the service for nothing.
"""

import pandas as pd
import streamlit as st

from config import config

VOTE_PROBLEM_COLUMN = "problem type"
VOTE_COUNT_COLUMN = "notes"


def render_machine_condition(machine_detail):
    profile = machine_detail["profile"]
    risk = machine_detail["risk"]

    st.subheader(profile["machine_code"] + " · " + profile["machine_type"])
    st.caption(
        profile["factory_name"] + " · " + profile["production_line"] + " · " + profile["usage_pattern"]
        + " use · " + str(int(profile["machine_age_months"])) + " months old"
    )
    with st.container(horizontal=True, width="content"):
        st.badge(risk["risk_band"] + " risk", color=config.RISK_BAND_BADGE_COLOURS.get(risk["risk_band"], "gray"))
        st.badge("Priority " + risk["priority"], color="blue")
        st.badge(risk["importance"], color="violet")

    with st.container(border=True):
        st.markdown("**Risk assessment**")
        probability_column, band_column, priority_column = st.columns(3)
        probability_column.metric(
            "Breakdown probability", risk["breakdown_probability"],
            help="Chance of a breakdown within 30 days, as judged by the breakdown risk model.")
        band_column.metric("Risk band", risk["risk_band"])
        priority_column.metric(
            "Priority", risk["priority"], help="The risk band crossed with machine importance (Policy 01).")

    with st.container(border=True):
        st.markdown("**Condition this week**")
        vibration_column, temperature_column, alarm_column = st.columns(3)
        vibration_column.metric("Average vibration", str(profile["average_vibration"]) + " mm/s")
        temperature_column.metric("Average temperature", str(profile["average_temperature_c"]) + " °C")
        alarm_column.metric("Alarms this week", int(profile["alarms_this_week"]))


def build_vote_table(problem_votes):
    """One row per problem type, the most supported first."""
    vote_table = pd.DataFrame(list(problem_votes.items()), columns=[VOTE_PROBLEM_COLUMN, VOTE_COUNT_COLUMN])
    return vote_table.sort_values(VOTE_COUNT_COLUMN, ascending=False, kind="stable").reset_index(drop=True)


def render_note_history(note_history):
    with st.container(border=True):
        st.markdown("**What the technician notes say**")
        if note_history["note_count"] == 0:
            st.write("No technician notes have been written for this machine.")
            return

        verdict_column, vote_column = st.columns([3, 2])
        with verdict_column:
            st.metric("Likely problem type", note_history["detected_problem_type"])
            st.caption(
                "Confidence " + str(note_history["confidence"]) + " from " + str(note_history["note_count"])
                + " past notes. The note-reading model considered every note written for this machine."
            )
        with vote_column:
            st.dataframe(
                build_vote_table(note_history["problem_votes"]).rename(
                    columns={VOTE_PROBLEM_COLUMN: "Problem type", VOTE_COUNT_COLUMN: "Notes"}),
                hide_index=True,
                width="stretch",
            )
        with st.expander("Most recent notes"):
            for note_text in note_history["recent_notes"]:
                st.markdown("- " + note_text)


def render_machine_detail_page(machine_detail):
    render_machine_condition(machine_detail)
    render_note_history(machine_detail["notes"])
