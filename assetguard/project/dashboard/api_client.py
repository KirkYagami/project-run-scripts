"""The dashboard's single point of contact with the AssetGuard AI service.

Every figure, repair job and decision shown in the dashboard arrives through one
of these functions. Nothing here reshapes, filters, sorts or rounds what the
service sent, and every unsuccessful reply is raised rather than hidden, apart
from the two deliberate exceptions: a refused sign in and an unknown machine.
"""

import requests
import streamlit as st

from config import config

# Where this browser tab keeps its session token, put there by the sign in page.
SESSION_TOKEN_KEY = "session_token"


def _address(path):
    return config.API_BASE_URL + path


def _get(path, query_values=None):
    response = requests.get(
        _address(path), params=query_values, headers=build_request_headers(),
        timeout=config.API_REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


def _post(path, body):
    response = requests.post(
        _address(path), json=body, headers=build_request_headers(), timeout=config.API_REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


# ---------------------------------------------------------------- signing in

def build_request_headers():
    """The one header naming who is asking; empty text when no token is held."""
    return {config.SESSION_TOKEN_HEADER: st.session_state.get(SESSION_TOKEN_KEY, "")}


def sign_in_user(username, password):
    """The signed in account as the service sent it, or {} when the details were refused."""
    response = requests.post(
        _address("/auth/signin"), json={"username": username, "password": password},
        timeout=config.API_REQUEST_TIMEOUT_SECONDS)
    if response.status_code == 401:
        return {}
    response.raise_for_status()
    return response.json()


def sign_out_user():
    """Tell the service to forget this tab's token; raises if it was not told."""
    return _post("/auth/signout", {})["signed_out"]


# ---------------------------------------------------------------- fleet and machines

def fetch_fleet_risk_table(risk_band):
    return _get("/fleet/risk", {"risk_band": risk_band})


def fetch_machine_detail(machine_code):
    """The profile, risk and notes for one machine, or {} when the service does not know it."""
    response = requests.get(
        _address("/machines/" + machine_code), headers=build_request_headers(),
        timeout=config.API_REQUEST_TIMEOUT_SECONDS)
    if response.status_code == 404:
        return {}
    response.raise_for_status()
    return {
        "profile": response.json(),
        "risk": _get("/machines/" + machine_code + "/risk"),
        "notes": _get("/machines/" + machine_code + "/notes"),
    }


# ---------------------------------------------------------------- advisory and review

def request_advisory_run(advisory_request):
    return _post("/advisories", advisory_request)


def fetch_repair_job_detail(repair_job_id):
    return _get("/repairjobs/" + repair_job_id)


def fetch_repair_jobs(status_value):
    return _get("/repairjobs", {"status_value": status_value})


def submit_supervisor_decision(repair_job_id, decision_payload):
    return _post("/repairjobs/" + repair_job_id + "/review", decision_payload)


def fetch_review_history(repair_job_id):
    return _get("/repairjobs/" + repair_job_id + "/reviews")


def fetch_call_budget(run_id):
    return _get("/runs/" + run_id + "/calls")


# ---------------------------------------------------------------- manual chat

def ask_manual_question(question_text, conversation_history):
    """One question to the manual assistant: exactly one language model call, never repeated."""
    return _post("/chat/ask", {"question": question_text, "history": conversation_history})


def fetch_recent_chat_turns(turn_limit):
    return _get("/audit/chat-turns", {"turn_limit": turn_limit})
