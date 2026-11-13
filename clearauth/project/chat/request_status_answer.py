import re
from collections import Counter
from config import config as c
from persistence.models import AuthorisationReview
from persistence.repository import fetch_review_records
from tools.letter_tools import _service
from tools.request_data_tools import canonical_request_reference


def answer_request_status(
    session,
    signed_in_user,
    open_requests,
    question_type,
    request_reference,
    member_number,
):
    if question_type not in c.CHAT_RECORD_TYPES:
        raise ValueError(f"Unknown record question {question_type}")
    role = signed_in_user["role"]
    if (
        role == c.ROLE_REPRESENTATIVE
        and question_type == c.CHAT_TYPE_OUTCOME_PREDICTION
    ):
        return c.CLINICAL_DETERMINATION_LINE
    if not request_reference:
        return (
            c.CHAT_REQUEST_NOT_NAMED_MESSAGE
            if role == c.ROLE_REPRESENTATIVE
            else c.CHAT_REVIEW_NOT_NAMED_MESSAGE
        )
    reference = canonical_request_reference(request_reference)
    if role == c.ROLE_REPRESENTATIVE:
        match = open_requests[open_requests[c.REQUEST_REFERENCE_COLUMN] == reference]
        if (
            match.empty
            or member_number is None
            or match.iloc[0][c.MEMBER_NUMBER_COLUMN] != member_number
        ):
            return c.CHAT_NO_CONFIRMATION_TEMPLATE.format(request_reference=reference)
        records = fetch_review_records(
            session, AuthorisationReview.request_reference == reference
        )
        record = records[0] if records else {}
        status = record.get("status", c.REVIEW_STATUS_AWAITING)
        reply = c.CHAT_REQUEST_CONFIRMED_TEMPLATE.format(
            request_reference=reference,
            service=_service(match.iloc[0].to_dict()),
            status=c.REVIEW_STATUS_LABELS[status].lower(),
        )
        if status == c.REVIEW_STATUS_INFORMATION_REQUESTED:
            reply += (
                "\n"
                + c.CHAT_ANSWERS_ASKED_FOR_TEXT
                + "\n"
                + "\n".join(record["letter_details"][c.CRITERIA_NOT_DOCUMENTED_DETAIL])
            )
        return reply
    if role not in c.ROLES_SEEING_EVERY_REVIEW:
        raise ValueError(f"Unknown role {role}")
    records = fetch_review_records(
        session, AuthorisationReview.request_reference == reference
    )
    if not records:
        return c.CHAT_NO_REVIEW_TEMPLATE.format(request_reference=reference)
    out = []
    for r in records:
        counts = Counter(f["evidence_type"] for f in r["evidence"])
        out.extend(
            [
                c.CHAT_REVIEW_TEMPLATE.format(
                    **dict(
                        r,
                        service=_service(r),
                        status=c.REVIEW_STATUS_LABELS[r["status"]],
                    )
                ),
                c.CHAT_SCREENING_TEMPLATE.format(
                    screening=r["screening"],
                    criteria="; ".join(
                        f"{x['criterion_name']}: {x['result']}" for x in r["criteria"]
                    ),
                    decisions_open=", ".join(r["decisions_open"]),
                ),
                c.CHAT_FIGURES_TEMPLATE.format(
                    approval_likelihood=f"{r['approval_likelihood']:.{c.LIKELIHOOD_DECIMALS}f}",
                    approval_band=r["approval_band"],
                    expected_stay=r["stay_text"],
                ),
                c.CHAT_EVIDENCE_TEMPLATE.format(
                    sentence_count=len(r["evidence"]),
                    evidence_counts=(
                        ", ".join(f"{k}: {v}" for k, v in sorted(counts.items()))
                        if counts
                        else c.CHAT_NO_DOCUMENTS_TEXT
                    ),
                    disagreement_count=len(r["disagreements"]),
                ),
                (
                    c.CHAT_AWAITING_DECISION_TEMPLATE.format(**r)
                    if r["decision"] is None
                    else c.CHAT_DECIDED_TEMPLATE.format(
                        **dict(
                            r,
                            decision_reason=re.sub(
                                c.MEMBER_NUMBER_IN_TEXT_PATTERN,
                                c.CHAT_MEMBER_NUMBER_WITHHELD_TEXT,
                                r["decision_reason"],
                            ),
                        )
                    )
                ),
            ]
        )
    return "\n".join(out)
