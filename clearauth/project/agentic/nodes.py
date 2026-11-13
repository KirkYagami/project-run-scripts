import secrets
import pandas as pd
from decimal import Decimal
from config import config as c
from persistence.database import session_factory
from persistence.repository import *
from modeling.model_registry import load_model, load_feature_schema
from knowledge.policy_reading import read_medical_policy
from knowledge.vector_index import open_vector_index
from tools.request_data_tools import *
from tools.screening_tools import screen_request
from tools.evidence_tools import *
from tools.prediction_tools import *
from tools.retrieval_tools import *
from tools.letter_tools import *
from tools.decision_tools import find_decision_refusal
from . import agents
from langgraph.types import interrupt

approval_model = load_model(c.APPROVAL_MODEL_FILE)
stay_model = load_model(c.STAY_MODEL_FILE)
evidence_model = load_model(c.EVIDENCE_MODEL_FILE)
approval_features = load_feature_schema(c.APPROVAL_SCHEMA_FILE)
stay_features = load_feature_schema(c.STAY_SCHEMA_FILE)
open_requests = load_open_requests()
request_notes = load_request_notes()
knowledge_collection = open_vector_index(c.VECTOR_STORE_DIRECTORY)
medical_policies = {
    code: read_medical_policy(code) for code in c.SERVICE_POLICY_DOCUMENTS
}


def plain(v):
    if isinstance(v, dict):
        return {k: plain(x) for k, x in v.items()}
    if isinstance(v, list):
        return [plain(x) for x in v]
    if v is None or pd.isna(v):
        return None
    if isinstance(v, Decimal):
        return float(v)
    if hasattr(v, "item"):
        return v.item()
    return v


def gather_request_context(request_reference):
    request = fetch_request(open_requests, request_reference)
    documents = fetch_request_documents(request_notes, request)
    policy = medical_policies[request[c.SERVICE_CODE_COLUMN]]
    screening = screen_request(request, policy)
    findings = link_evidence_to_criteria(
        read_document_evidence(evidence_model, documents), screening
    )
    return dict(
        request_profile=request,
        request_documents=documents,
        screening=screening,
        evidence_findings=findings,
        disagreements=flag_document_disagreements(findings, request, policy),
        likelihood=estimate_approval_likelihood(
            approval_model, approval_features, request, screening
        ),
        stay=(
            estimate_expected_stay(stay_model, stay_features, request, screening)
            if request[c.SITE_OF_SERVICE_COLUMN] == c.INPATIENT_SITE
            else {}
        ),
    )


def load_request_context_node(state):
    context = gather_request_context(state["request_reference"])
    run = c.RUN_ID_PREFIX + secrets.token_hex(c.IDENTIFIER_HEX_LENGTH // 2).upper()
    review = (
        c.REVIEW_ID_PREFIX + secrets.token_hex(c.IDENTIFIER_HEX_LENGTH // 2).upper()
    )
    with session_factory.begin() as session:
        insert_agent_run(
            session,
            {
                k: state[k]
                for k in [
                    "thread_id",
                    "request_reference",
                    "coordinator_request",
                    "coordinator_id",
                ]
            }
            | dict(run_id=run, status=c.AGENT_RUN_STATUS_RUNNING, llm_call_count=0),
        )
    return dict(run_id=run, review_id=review, **context)


def _record(state, result):
    with session_factory.begin() as session:
        insert_llm_call(session, state["run_id"], result["call_record"])
    return {k: v for k, v in result.items() if k != "call_record"} | dict(
        llm_call_count=1
    )


def plan_review_node(s):
    return _record(
        s,
        agents.plan_review(
            s["request_profile"],
            s["request_documents"],
            s["screening"]["policy_document"],
            s["coordinator_request"],
        ),
    )


def assess_criteria_node(s):
    return _record(
        s,
        agents.analyse_criteria(s["screening"], s["request_profile"], s["review_plan"]),
    )


def review_evidence_node(s):
    types = list(
        dict.fromkeys(
            f["evidence_type"]
            for f in s["evidence_findings"]
            if f["evidence_type"] in c.EVIDENCE_GUIDE_DOCUMENTS
        )
    )
    checks = {t: read_reviewer_checks(knowledge_collection, t) for t in types}
    return _record(
        s,
        agents.review_evidence(
            s["evidence_findings"],
            s["disagreements"],
            checks,
            s["request_profile"],
            s["screening"],
            s["review_plan"],
        ),
    )


def weigh_predictions_node(s):
    return _record(
        s,
        agents.analyse_predictions(
            s["likelihood"],
            s["stay"],
            s["request_profile"],
            s["screening"],
            s["review_plan"],
        ),
    )


def compose_review_recommendation_node(s):
    result = agents.write_review_recommendation(
        *[
            s[k]
            for k in [
                "request_profile",
                "coordinator_request",
                "screening",
                "likelihood",
                "stay",
                "review_plan",
                "criteria_analysis",
                "evidence_review",
                "prediction_analysis",
            ]
        ]
    )
    screen = s["screening"]
    r = s["request_profile"]
    stay = s["stay"]
    record = {
        k: screen[k]
        for k in [
            "request_reference",
            "service_code",
            "policy_document",
            "body_mass_index",
            "criteria",
            "screening",
            "decisions_open",
        ]
        + c.CRITERIA_COUNT_COLUMNS
    }
    record.update(
        review_id=s["review_id"],
        run_id=s["run_id"],
        service_name=c.SERVICE_NAMES[r[c.SERVICE_CODE_COLUMN]],
        urgency=r[c.URGENCY_COLUMN],
        evidence=s["evidence_findings"],
        disagreements=s["disagreements"],
        **s["likelihood"],
        expected_stay_days=stay.get("expected_stay_days"),
        requested_inpatient_days=stay.get("requested_inpatient_days"),
        longer_stay_expected=stay.get("longer_stay_expected"),
        stay_text=describe_expected_stay(stay, r[c.SITE_OF_SERVICE_COLUMN]),
        coordinator_request=s["coordinator_request"],
        recommendation_text=result["review_recommendation"]["RECOMMENDATION"],
        recommended_decision=result["review_recommendation"]["RECOMMENDED DECISION"],
        status=c.REVIEW_STATUS_AWAITING
    )
    for key, target in [
        ("review_plan", "review_plan_text"),
        ("criteria_analysis", "criteria_analysis_text"),
        ("evidence_review", "evidence_review_text"),
        ("prediction_analysis", "prediction_analysis_text"),
    ]:
        record[target] = agents.join_labelled_response(s[key])
    with session_factory.begin() as session:
        insert_llm_call(session, s["run_id"], result["call_record"])
        insert_authorisation_review(session, plain(record))
        update_agent_run(
            session,
            s["run_id"],
            c.AGENT_RUN_STATUS_AWAITING_DECISION,
            s.get("llm_call_count", 0) + 1,
        )
    return dict(llm_call_count=1)


def request_review_decision_node(s):
    decision = interrupt({"review_id": s["review_id"]})
    refusal = find_decision_refusal(
        decision, s["screening"], s["request_profile"], s["coordinator_id"]
    )
    if refusal:
        raise ValueError(refusal)
    return dict(
        review_decision=decision, office_letter={}, letter_details={}, member_notice={}
    )


def route_review_decision(s):
    return s["review_decision"]["decision"]


def draft_office_letter_node(s):
    decision = s["review_decision"]["decision"]
    r = s["request_profile"]
    screen = s["screening"]
    details = (
        build_authorisation_details(r, screen["policy_document"])
        if decision == c.DECISION_APPROVE
        else build_information_request_details(
            r,
            screen,
            read_documentation_to_send(knowledge_collection, r[c.SERVICE_CODE_COLUMN]),
        )
    )
    return _record(s, agents.draft_office_letter(decision, r, details)) | dict(
        letter_details=details
    )


def draft_member_notice_node(s):
    return _record(s, agents.draft_member_notice(s["request_profile"], s["screening"]))


def record_review_outcome_node(s):
    from persistence.models import ReviewDecision
    from sqlalchemy import select

    decision = s["review_decision"]
    d = decision["decision"]
    with session_factory.begin() as session:
        if session.scalars(
            select(ReviewDecision).where(ReviewDecision.review_id == s["review_id"])
        ).first():
            return {}
        insert_review_decision(
            session, dict(decision, review_id=s["review_id"], run_id=s["run_id"])
        )
        record_review_outcome(
            session,
            s["review_id"],
            dict(
                status=c.REVIEW_STATUS_BY_DECISION[d],
                letter_text=(
                    agents.join_labelled_response(s["office_letter"])
                    if s["office_letter"]
                    else None
                ),
                letter_details=s["letter_details"] or None,
                notice_text=(
                    agents.join_labelled_response(s["member_notice"])
                    if s["member_notice"]
                    else None
                ),
                referral_summary=(
                    plain(
                        dict(
                            criteria=s["screening"]["criteria"],
                            evidence=s["evidence_findings"],
                            disagreements=s["disagreements"],
                        )
                    )
                    if d == c.DECISION_REFER
                    else None
                ),
            ),
        )
        update_agent_run(
            session, s["run_id"], c.AGENT_RUN_STATUS_COMPLETE, s["llm_call_count"]
        )
    return {}
