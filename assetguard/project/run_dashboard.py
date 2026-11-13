"""Entry point 6: the AssetGuard AI dashboard.

Run from the Project folder with:  python3 -m streamlit run run_dashboard.py
The port, address and look come from .streamlit/config.toml beside this file.
Every figure is asked for from the service through dashboard/api_client.py.
"""

import requests
import streamlit as st

from access.permissions import resolve_pages_for_role
from config import config
from dashboard.api_client import (
    SESSION_TOKEN_KEY,
    ask_manual_question,
    fetch_call_budget,
    fetch_fleet_risk_table,
    fetch_machine_detail,
    fetch_recent_chat_turns,
    fetch_repair_job_detail,
    fetch_repair_jobs,
    fetch_review_history,
    request_advisory_run,
    sign_in_user,
    sign_out_user,
    submit_supervisor_decision,
)
from dashboard.audit_trail import render_audit_trail_page, render_call_budget, render_chat_log, render_decision_detail
from dashboard.fleet_overview import BAND_CHOICE_ALL, render_fleet_overview_page
from dashboard.machine_detail import render_machine_detail_page
from dashboard.manual_chat import render_manual_chat_page
from dashboard.review_queue import render_review_queue_page

PAGE_FLEET = config.PAGE_FLEET
PAGE_MACHINE = config.PAGE_MACHINE
PAGE_REVIEW = config.PAGE_REVIEW
PAGE_AUDIT = config.PAGE_AUDIT
PAGE_CHAT = config.PAGE_CHAT

# Matched to the pages by name, so each line stays with its page whatever a role's list holds.
PAGE_DESCRIPTIONS = {
    PAGE_FLEET: "Which machines are closest to failing",
    PAGE_MACHINE: "One machine in depth, and raise a repair job",
    PAGE_REVIEW: "Approve, modify or reject drafted repair jobs",
    PAGE_AUDIT: "What was decided, what changed, what it cost",
    PAGE_CHAT: "Ask the manuals a question",
}

DISPLAY_NAME_KEY = "display_name"
ROLE_KEY = "role"
DEFAULT_REQUEST_TEXT = (
    "Investigate the risk on this machine and draft a repair job with the procedure, permit, parts and "
    "a proposed window."
)
START_SERVICE_COMMAND = "cd Project\npython3 run_api_service.py"

# Filled by render_signed_in_sidebar: a slot above sign out for a page's own sidebar controls.
sidebar_page_controls = None


# ---------------------------------------------------------------- session

def render_sign_in_page():
    st.title(config.DASHBOARD_TITLE)
    st.caption(config.DASHBOARD_SUBTITLE)
    with st.form("sign-in"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", type="primary")
    if not submitted:
        return

    account = sign_in_user(username.strip(), password)
    if not account:
        st.error(config.SIGN_IN_FAILED_MESSAGE)
        return
    st.session_state[SESSION_TOKEN_KEY] = account["session_token"]
    st.session_state[DISPLAY_NAME_KEY] = account["display_name"]
    st.session_state[ROLE_KEY] = account["role"]
    st.rerun()


def render_signed_in_sidebar():
    """Draw the sidebar and return the page chosen; sign out sits last."""
    global sidebar_page_controls
    with st.sidebar:
        st.title(config.DASHBOARD_TITLE)
        st.caption(config.DASHBOARD_SUBTITLE)
        st.markdown("**" + st.session_state[DISPLAY_NAME_KEY] + "** · " + st.session_state[ROLE_KEY])
        st.divider()
        allowed_pages = resolve_pages_for_role(st.session_state[ROLE_KEY])
        chosen_page = st.radio(
            "Page", allowed_pages,
            captions=[PAGE_DESCRIPTIONS.get(page_name, "") for page_name in allowed_pages],
            label_visibility="collapsed",
        )
        sidebar_page_controls = st.container()
        st.divider()
        if st.button("Sign out", width="stretch"):
            try:
                sign_out_user()
            except requests.RequestException as sign_out_error:
                st.error("Sign out did not reach the service, so the session is still live: " + str(sign_out_error))
            else:
                st.session_state.clear()
                st.rerun()
    return chosen_page


def render_service_warning(connection_error):
    with st.container(border=True):
        st.error("The AssetGuard AI service is not answering at " + config.API_BASE_URL + ".")
        st.markdown("Start it in a second terminal from the Project folder, then reload this page:")
        st.code(START_SERVICE_COMMAND, language="bash")
        st.caption("Underlying error: " + str(connection_error))


# ---------------------------------------------------------------- pages

def render_fleet_page():
    render_fleet_overview_page(fetch_fleet_risk_table(BAND_CHOICE_ALL))


def render_machine_page():
    high_risk_rows = fetch_fleet_risk_table(config.RISK_BAND_HIGH)
    if not high_risk_rows:
        st.header(PAGE_MACHINE)
        st.info("No machine is in the HIGH band, so there is nothing to inspect.")
        return

    with sidebar_page_controls:
        st.divider()
        machine_code = st.selectbox(
            "High risk machine",
            [row["machine_code"] for row in high_risk_rows],
            help="The HIGH band of the scored fleet, the worst at the top.",
        )
    machine_detail = fetch_machine_detail(machine_code)
    if not machine_detail:
        st.warning(machine_code + " was not found in the current fleet.")
        return
    render_machine_detail_page(machine_detail)

    with st.container(border=True):
        st.markdown("**Raise a repair job**")
        st.caption(
            "Five agents investigate in turn, then the run pauses for a decision on the " + PAGE_REVIEW
            + " page. This costs five language model calls."
        )
        request_text = st.text_area("Request to the agents", value=DEFAULT_REQUEST_TEXT)
        access_level = st.radio(
            "Access difficulty", config.ACCESS_LEVEL_OPTIONS,
            index=len(config.ACCESS_LEVEL_OPTIONS) // 2, horizontal=True,
            help="Safety Rule 03: tight space work takes longer, so its downtime estimate is stretched.",
        )
        if not st.button("Start advisory run", type="primary"):
            return
        with st.spinner("Five agents are working. Five language model calls are being made..."):
            repair_job = request_advisory_run({
                "machine_code": machine_code,
                "request_text": request_text,
                "access_level": access_level,
            })
        st.success(
            "Draft " + repair_job["repair_job_id"] + " is waiting on the " + PAGE_REVIEW
            + " page. Nothing is issued until a supervisor decides it there."
        )


def render_review_page():
    render_review_queue_page(fetch_repair_jobs(config.REPAIR_JOB_STATUS_PENDING), submit_supervisor_decision)


def render_audit_page():
    approved_jobs = fetch_repair_jobs(config.REPAIR_JOB_STATUS_APPROVED)
    rejected_jobs = fetch_repair_jobs(config.REPAIR_JOB_STATUS_REJECTED)
    render_audit_trail_page(approved_jobs, rejected_jobs)

    decided_jobs = approved_jobs + rejected_jobs
    if decided_jobs:
        repair_job_id = st.selectbox("Open a decided repair job", [job["repair_job_id"] for job in decided_jobs])
        decided_job = fetch_repair_job_detail(repair_job_id)
        render_decision_detail(decided_job, fetch_review_history(repair_job_id))
        render_call_budget(fetch_call_budget(decided_job["run_id"]))

    render_chat_log(fetch_recent_chat_turns(config.CHAT_AUDIT_RECENT_ROWS))


def render_chat_page():
    render_manual_chat_page(ask_manual_question)


PAGE_RENDERERS = {
    PAGE_FLEET: render_fleet_page,
    PAGE_MACHINE: render_machine_page,
    PAGE_REVIEW: render_review_page,
    PAGE_AUDIT: render_audit_page,
    PAGE_CHAT: render_chat_page,
}


# ---------------------------------------------------------------- main

st.set_page_config(page_title=config.DASHBOARD_TITLE, page_icon="🏭", layout="wide")

try:
    if not st.session_state.get(SESSION_TOKEN_KEY):
        render_sign_in_page()
    else:
        PAGE_RENDERERS[render_signed_in_sidebar()]()
except requests.HTTPError as reply_error:
    status_code = reply_error.response.status_code if reply_error.response is not None else 500
    if status_code < 500:
        # The service answered but refused: say what it said rather than claim it is down.
        st.error("The service refused that request: " + reply_error.response.text)
    elif status_code == 503:
        # The service is up; the language model behind it is not.
        st.warning(reply_error.response.json().get("detail", reply_error.response.text))
    else:
        render_service_warning(reply_error)
except requests.RequestException as connection_error:
    render_service_warning(connection_error)
