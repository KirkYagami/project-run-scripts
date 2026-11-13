"""Offline integration smoke checks; mocks only the external language-model boundary."""

import tempfile
from pathlib import Path
from unittest.mock import patch
from config import config as c

sandbox = Path(tempfile.mkdtemp(prefix="clearauth-smoke-"))
c.DATABASE_DIRECTORY = str(sandbox)
c.APPLICATION_DATABASE_FILE = str(sandbox / "app.db")
c.APPLICATION_DATABASE_URL = "sqlite:///" + c.APPLICATION_DATABASE_FILE
c.CHECKPOINT_DATABASE_FILE = str(sandbox / "checkpoint.db")
from run_database_setup import main

main()
from api.routes import service_application, review_workflow, request_details
from agentic import agents
from fastapi.testclient import TestClient
from tools.letter_tools import build_authorisation_details


def fake(prompt_text, agent_name):
    import json

    facts = json.loads(prompt_text.split("ESTABLISHED FACTS:\n")[-1])
    outputs = {
        c.AGENT_NAME_PLANNER: "PRIORITY: Review the supplied questionnaire under its own medical policy.\nCHECKS: Confirm the documented answers and evidence without replacing any answer.\nRATIONALE: Every result is established by deterministic tools before independent review.",
        c.AGENT_NAME_CRITERIA: "CRITERIA MET: Use the supplied criterion results exactly as established.\nCRITERIA NOT MET: Use only the established failed criteria in the screening.\nNOT DOCUMENTED: Ask for the blank answers required by the policy.\nCRITERIA SUMMARY: No questionnaire answer is filled from a document.",
        c.AGENT_NAME_EVIDENCE: "EVIDENCE FOUND: Read each submitted sentence and its linked criteria in order.\nDISAGREEMENTS: Flag only the supplied disagreements for the nurse to review.\nCHECKS TO MAKE: Use the supplied evidence guides and checks.\nEVIDENCE SUMMARY: Documents do not replace or fill questionnaire answers.",
        c.AGENT_NAME_PREDICTIONS: "LIKELIHOOD: Interpret the supplied likelihood as a historical estimate only.\nEXPECTED STAY: Use the supplied stay description without inventing any figure.\nPREDICTION SUMMARY: Neither figure is a reason for the decision on this request.",
    }
    if agent_name == c.AGENT_NAME_WRITER:
        outputs[agent_name] = (
            "RECOMMENDATION: Review the established screening and evidence before recording an independent nurse decision.\nRECOMMENDED DECISION: "
            + facts["screening"]["screening"]
        )
    if agent_name == c.AGENT_NAME_LETTER:
        details = facts["details"]
        ref = details[c.REQUEST_REFERENCE_DETAIL]
        service = details[c.SERVICE_DETAIL]
        outputs[agent_name] = (
            f"SUBJECT: {ref} {service}\nLETTER: The clinical review team has recorded the supplied decision for this request. Please read the following details and retain this correspondence for your records.\n"
            + "\n".join(
                k + ": " + ("; ".join(v) if isinstance(v, list) else str(v))
                for k, v in details.items()
            )
            + "\n"
            + c.LETTER_SIGN_OFF
        )
    if agent_name == c.AGENT_NAME_NOTICE:
        outputs[agent_name] = (
            f"HEADLINE: Your {facts['service']} is authorised\nNOTICE: Your {facts['service']} is authorised at {facts['place']}. Please contact your requesting office to arrange the service and discuss the next steps for your appointment.\n{c.LETTER_SIGN_OFF}"
        )
    text = outputs[agent_name]
    return dict(
        response_text=text,
        call_record=dict(
            agent_name=agent_name,
            model_name="offline-test-double",
            prompt_characters=len(prompt_text),
            response_characters=len(text),
            latency_milliseconds=0,
        ),
    )


client = TestClient(service_application)


def signin(user, password):
    r = client.post("/auth/signin", json={"username": user, "password": password})
    assert r.status_code == 200, r.text
    return {c.SESSION_TOKEN_HEADER: r.json()["session_token"]}


coordinator = signin("carlos", "22222222")
nurse = signin("leena", "11111111")
with patch.object(agents, "call_language_model", side_effect=fake):
    for decision in c.DECISIONS:
        choices = [
            (ref, d)
            for ref, d in request_details.items()
            if d["screening"]["screening"] == decision
            and (
                decision != c.DECISION_APPROVE
                or (
                    d["request"][c.SITE_OF_SERVICE_COLUMN] != c.NOT_GIVEN_TEXT
                    and (
                        d["request"][c.SITE_OF_SERVICE_COLUMN] != c.INPATIENT_SITE
                        or d["request"][c.REQUESTED_INPATIENT_DAYS_COLUMN]
                        != c.NOT_GIVEN_TEXT
                    )
                )
            )
        ]
        assert choices, decision
        ref, d = choices[0]
        r = client.post(
            "/reviews",
            headers=coordinator,
            json={
                "request_reference": ref,
                "coordinator_request": "Check all questionnaire criteria and clinical evidence.",
            },
        )
        assert r.status_code == 201, r.text
        record = r.json()
        review = record["review_id"]
        cfg = {"configurable": {"thread_id": record["thread_id"]}}
        assert (
            record["status"] == c.REVIEW_STATUS_AWAITING
            and record["letter_text"] is None
        )
        from agentic.graph import build_workflow

        fresh = build_workflow(c.CHECKPOINT_DATABASE_FILE)
        assert fresh.get_state(cfg).next == ("request_review_decision",)
        r = client.post(
            "/reviews/" + review + "/decision",
            headers=nurse,
            json={
                "decision": decision,
                "decision_reason": "I reviewed the supplied criteria and evidence and record this permitted outcome.",
            },
        )
        assert r.status_code == 200, r.text
        assert r.json()["status"] == c.REVIEW_STATUS_BY_DECISION[decision]
        budget = client.get("/reviews/" + review + "/calls", headers=coordinator).json()
        assert budget["call_count"] == c.LLM_CALLS_BY_DECISION[decision], budget
        r = client.post(
            "/reviews/" + review + "/decision",
            headers=nurse,
            json={
                "decision": decision,
                "decision_reason": "I reviewed the supplied criteria and evidence and record this permitted outcome.",
            },
        )
        assert r.status_code == 409, r.text
        assert not fresh.get_state(cfg).next
        print("PASS offline branch:", decision, "calls:", budget["call_count"])
print(
    "All offline workflow branches, restart persistence and duplicate-decision checks passed."
)
