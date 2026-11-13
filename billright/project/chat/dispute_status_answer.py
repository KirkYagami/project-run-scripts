"""Answers a question about one named dispute from its record, in the way the asker's role allows."""
from config import config
from persistence import repository
from persistence.models import BillingDispute


def _answer(text):
    return {"answer": text, "source_documents": [], "was_refused": False}


def answer_dispute_status(session, open_disputes, role_name, dispute_reference):
    """Answer a question about one named dispute from its record."""
    known = (dispute_reference is not None and
             (open_disputes[config.DISPUTE_REFERENCE_COLUMN] == dispute_reference).any())
    if not known:
        return _answer(config.CHAT_UNKNOWN_DISPUTE_MESSAGE)
    records = repository.fetch_dispute_records(session, BillingDispute.dispute_reference == dispute_reference)
    figures = role_name in config.CHAT_FIGURE_ROLES
    if not records:
        text = config.CHAT_NOT_ASSESSED_TEMPLATE.format(dispute_reference=dispute_reference)
        return _answer(text if figures else text + " " + config.CHAT_AMOUNTS_IN_WRITING_MESSAGE)
    record = records[0]
    if not figures:
        changed = record["decided_at"] or record["created_at"]
        text = config.CHAT_STATUS_TEMPLATE.format(
            dispute_reference=dispute_reference,
            status_phrase=config.CHAT_STATUS_PHRASES[record["status"]],
            changed_on=changed.strftime(config.STATUS_CHANGE_TIME_FORMAT))
        return _answer(text + " " + config.CHAT_AMOUNTS_IN_WRITING_MESSAGE)
    lines = [
        f"{dispute_reference}: assessment {record['assessment_id']}, status {record['status']}.",
        f"Amount billed GBP {record['amount_billed_gbp']}, corrected charge GBP {record['corrected_charge_gbp']}, "
        f"difference GBP {record['difference_gbp']} ({record['direction']}), redress GBP {record['redress_gbp']}.",
        f"Rebill probability {record['rebill_probability']} ({record['rebill_band']}); category "
        f"{record['dispute_category']}, with the notes agreeing {record['cause_agreement']}.",
        f"Effort {record['effort_needed_hours']} hours; recommended decision {record['recommended_decision']}.",
    ]
    if record["decision"]:
        lines.append(f"Decision {record['decision']} by {record['decided_by']} ({record['decided_by_role']}); "
                     f"settled amount GBP {record['settled_amount_gbp']} ({record['settlement_direction']}).")
    return _answer("\n".join(lines))
