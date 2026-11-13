"""The language model client, the reply parser, and the seven prompts.

Each prompt hands an agent facts that are already established and asks for prose in a fixed
layout of labelled fields, so the reply can be read back reliably. No agent calculates
anything: every figure it is shown was established by the models, the documents and the tools.
"""
import os
import re
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

from config import config

load_dotenv()

generation_settings = types.GenerateContentConfig(
    max_output_tokens=config.GEMINI_MAX_OUTPUT_TOKENS,
    temperature=config.GEMINI_TEMPERATURE,
    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
)


# ------------------------------------------------------------------ the client
def call_language_model(prompt_text, agent_name):
    """Make one language model call and return the reply and what the call cost."""
    api_key = os.environ.get(config.GEMINI_API_KEY_VARIABLE, "").strip()
    model_name = os.environ.get(config.GEMINI_MODEL_VARIABLE, "").strip()
    if not api_key or not model_name:
        raise ValueError(f"The language model cannot be called: set {config.GEMINI_API_KEY_VARIABLE} "
                         f"and {config.GEMINI_MODEL_VARIABLE} in .env.")
    started = time.perf_counter()
    with genai.Client(api_key=api_key) as client:
        response = client.models.generate_content(model=model_name, contents=prompt_text,
                                                  config=generation_settings)
        reply = (response.text or "").strip()
        finish = None
        if getattr(response, "candidates", None):
            finish = response.candidates[0].finish_reason
    latency = int(round((time.perf_counter() - started) * 1000))
    if not reply:
        raise ValueError(f"The {agent_name} agent got an empty reply from {model_name}.")
    if finish is not None and getattr(finish, "name", str(finish)) != "STOP":
        raise ValueError(f"The {agent_name} agent's reply from {model_name} did not finish "
                         f"normally ({getattr(finish, 'name', finish)}).")
    return {"response_text": reply,
            "call_record": {"agent_name": agent_name, "model_name": model_name,
                            "prompt_characters": len(prompt_text),
                            "response_characters": len(reply),
                            "latency_milliseconds": latency}}


# ------------------------------------------------------------------ the parser
def parse_labelled_response(response_text, field_labels, agent_name):
    """Read a labelled reply back into fields, tolerantly."""
    decoration = re.escape(config.RESPONSE_DECORATION_CHARACTERS)
    ordered = sorted(field_labels, key=len, reverse=True)
    patterns = [(label, re.compile(rf"^[{decoration}]*{re.escape(label)}[{decoration}]*:(.*)$",
                                   re.IGNORECASE)) for label in ordered]
    fields = {label: [] for label in field_labels}
    current = None
    for line in str(response_text).splitlines():
        matched = None
        for label, pattern in patterns:
            found = pattern.match(line)
            if found:
                matched = (label, found.group(1))
                break
        if matched:
            current = matched[0]
            text = matched[1].strip(config.RESPONSE_DECORATION_CHARACTERS)
            if text:
                fields[current].append(text)
        elif current is not None:
            fields[current].append(line.rstrip())
    result = {}
    for label in field_labels:
        value = "\n".join(fields[label]).strip()
        if not value:
            raise ValueError(f"The {agent_name} agent's reply is missing or leaves empty one of "
                             f"{list(field_labels)}: '{label}'.")
        result[label] = value
    return result


# ------------------------------------------------------------------ prompt helpers
def _value(profile, column):
    value = profile.get(column)
    try:
        if value != value:      # NaN
            return "not recorded"
    except Exception:
        pass
    return "not recorded" if value is None else str(value)


def _flag(profile, column):
    return _value(profile, column)


def _yes_no(flag):
    return config.BOOLEAN_LABELS[bool(flag)]


def _facts_block(profile):
    lines = [
        f"Dispute reference: {_value(profile, config.DISPUTE_REFERENCE_COLUMN)}",
        f"Billing centre: {_value(profile, 'billing_centre')}",
        f"Contact channel: {_value(profile, 'contact_channel')}",
        f"Bill period: {_value(profile, config.BILL_START_COLUMN)} to {_value(profile, config.BILL_END_COLUMN)}"
        f" ({_value(profile, config.DAYS_BILLED_COLUMN)} days, {_value(profile, 'billing_frequency')})",
        f"Billed tariff: {_value(profile, config.BILLED_TARIFF_COLUMN)}",
        f"Entitled tariff: {_value(profile, config.ENTITLED_TARIFF_COLUMN)}",
        f"Fixed term last day: {_value(profile, config.FIXED_TERM_LAST_DAY_COLUMN)}",
        f"Meter type: {_value(profile, config.METER_TYPE_COLUMN)}; smart meter: {_flag(profile, 'smart_meter_flag')}",
        f"Opening read type: {_value(profile, 'opening_read_type')}; closing read type: "
        f"{_value(profile, 'closing_read_type')}",
        f"Consecutive estimated bills: {_value(profile, 'consecutive_estimated_bills')}; "
        f"days since the last actual read: {_value(profile, 'days_since_last_actual_read')}",
        f"Amount billed: GBP {_value(profile, config.AMOUNT_BILLED_COLUMN)}",
        f"Priority Services Register: {_flag(profile, config.PRIORITY_SERVICES_COLUMN)}",
    ]
    return "\n".join(lines)


def _reads_block(profile):
    return "\n".join([
        f"Reads on the bill: opening {_value(profile, config.OPENING_READ_COLUMN)}, closing "
        f"{_value(profile, config.CLOSING_READ_COLUMN)}, night opening "
        f"{_value(profile, config.NIGHT_OPENING_READ_COLUMN)}, night closing "
        f"{_value(profile, config.NIGHT_CLOSING_READ_COLUMN)}, billed units {_value(profile, config.BILLED_UNITS_COLUMN)} kWh",
        f"Verified reads ({_value(profile, config.VERIFIED_READ_SOURCE_COLUMN)}): opening "
        f"{_value(profile, config.VERIFIED_OPENING_READ_COLUMN)}, closing "
        f"{_value(profile, config.VERIFIED_CLOSING_READ_COLUMN)}, night opening "
        f"{_value(profile, config.VERIFIED_NIGHT_OPENING_READ_COLUMN)}, night closing "
        f"{_value(profile, config.VERIFIED_NIGHT_CLOSING_READ_COLUMN)}",
        f"Register digits: {_value(profile, config.REGISTER_DIGITS_COLUMN)}",
    ])


def _standards_block(profile):
    return "\n".join(f"{code} ({config.GUARANTEED_STANDARD_BREACH_PHRASES[code]}): "
                     f"{_value(profile, column)}"
                     for code, column in config.GUARANTEED_STANDARD_BREACH_COLUMNS.items())


def _fields_text(fields):
    return "\n".join(f"{label}: {text}" for label, text in fields.items())


def _layout(labels):
    return "\n".join(f"{label}: <your text>" for label in labels)


_NO_FIGURES = ("Use only the figures you are given. Do not calculate, recalculate, round, derive "
               "or invent any figure.")


def _ask(prompt, labels, agent_name):
    reply = call_language_model(prompt, agent_name)
    return parse_labelled_response(reply["response_text"], labels, agent_name), reply["call_record"]


# ------------------------------------------------------------------ the seven agents
def plan_assessment(dispute_profile, analyst_request):
    """Decide what has to be established about this dispute before anyone can decide anything."""
    labels = ["PRIORITY", "CHECKS", "RATIONALE"]
    prompt = (
        f"You are the intake planner for {config.ORGANISATION_NAME}'s billing disputes desk. You plan; "
        "you settle nothing and you decide nothing.\n\n"
        f"THE DISPUTE\n{_facts_block(dispute_profile)}\n\n"
        f"THE READS\n{_reads_block(dispute_profile)}\n\n"
        f"THE STANDARDS THE RECORD FLAGS\n{_standards_block(dispute_profile)}\n\n"
        f"THE ANALYST'S REQUEST\n{analyst_request}\n\n"
        "Decide what has to be established about this dispute before a decision can be made. Write several "
        "full sentences. Reply in exactly this layout, one label per line start:\n"
        f"{_layout(labels)}\n"
        "PRIORITY is one word: HIGH, MEDIUM or LOW. CHECKS lists what must be checked. RATIONALE says why.\n"
        + _NO_FIGURES)
    fields, record = _ask(prompt, labels, config.AGENT_NAME_PLANNER)
    return {"assessment_plan": fields, "call_record": record}


def assess_rebill_risk(rebill_facts, dispute_profile, assessment_plan):
    """Explain what is driving the rebill score, in terms a Revenue Controller can act on."""
    labels = ["DRIVERS", "READS", "REBILL SUMMARY"]
    prompt = (
        f"You are the rebill analyst for {config.ORGANISATION_NAME}. Explain what is driving the rebill "
        "score so a Revenue Controller can act on it.\n\n"
        f"REBILL SCORE\nProbability of a corrected bill: {rebill_facts['rebill_probability']}\n"
        f"Band: {rebill_facts['rebill_band']} (HIGH at or above {config.REBILL_BAND_HIGH_THRESHOLD}, "
        f"MEDIUM at or above {config.REBILL_BAND_MEDIUM_THRESHOLD}, otherwise LOW)\n\n"
        f"THE FACTS THE MODEL READ\n{_facts_block(dispute_profile)}\n"
        f"Prior disputes in twelve months: {_value(dispute_profile, 'prior_disputes_12m')}\n"
        f"Tariff changes in the bill: {_value(dispute_profile, 'tariff_changes_in_bill')}; days of a "
        f"fixed term cut short: {_value(dispute_profile, 'fixed_term_days_cut_short')}\n\n"
        f"THE PLAN'S CHECKS\n{assessment_plan['CHECKS']}\n\n"
        "The score is a prediction from the bill's facts. It does not say whether the bill was wrong; "
        "the corrected charge settles that. Write several full sentences. Reply in exactly this layout:\n"
        f"{_layout(labels)}\n" + _NO_FIGURES)
    fields, record = _ask(prompt, labels, config.AGENT_NAME_REBILL)
    return {"rebill_assessment": fields, "call_record": record}


def identify_cause(cause_facts, dispute_profile, assessment_plan, rebill_assessment):
    """Say how much weight the category the notes name deserves."""
    labels = ["DISPUTE CATEGORY", "CONFIDENCE", "EVIDENCE"]
    notes = "\n".join(f"Note {index + 1}: {category}"
                      for index, category in enumerate(cause_facts["note_categories"]))
    prompt = (
        f"You are the cause analyst for {config.ORGANISATION_NAME}. Say how much weight the category "
        "named by the contact notes deserves.\n\n"
        f"CAUSE FACTS\nCategory named by most notes: {cause_facts['dispute_category']}\n"
        f"Agreement: {cause_facts['agreement']} of {cause_facts['notes_read']} notes read; "
        f"{cause_facts['notes_too_short_to_read']} too short to read\n{notes}\n"
        f"Other categories named: {', '.join(cause_facts['other_categories']) or 'none'}\n\n"
        f"ACCOUNT FACTS THAT BEAR ON THE CATEGORY\n{_facts_block(dispute_profile)}\n\n"
        f"THE PLAN'S CHECKS\n{assessment_plan['CHECKS']}\n\n"
        f"THE REBILL AGENT'S SUMMARY\n{rebill_assessment['REBILL SUMMARY']}\n\n"
        f"THE CATEGORIES: {', '.join(config.DISPUTE_CATEGORIES)}\n\n"
        "An agreement below about half means the notes disagree, and you must say so. Write several full "
        f"sentences. Reply in exactly this layout:\n{_layout(labels)}\n" + _NO_FIGURES)
    fields, record = _ask(prompt, labels, config.AGENT_NAME_CAUSE)
    return {"cause_analysis": fields, "call_record": record}


def _piece_lines(pieces):
    lines = []
    for number, piece in enumerate(pieces, start=1):
        window = piece["price_window"]
        if "unit_rate_pence" in window:
            prices = (f"{window['unit_rate_pence']}p per kWh, {window['standing_charge_pence']}p per day; "
                      f"usage {piece['units_kwh']} kWh")
        else:
            prices = (f"day {window['day_unit_rate_pence']}p and night {window['night_unit_rate_pence']}p per "
                      f"kWh, {window['standing_charge_pence']}p per day; usage day {piece['day_units_kwh']} kWh, "
                      f"night {piece['night_units_kwh']} kWh")
        lines.append(f"Piece {number}: {piece['tariff']}, {piece['first_day']} to {piece['last_day']}, "
                     f"{piece['days']} days, prices from {window['opens_on']}: {prices}; "
                     f"charge {piece['charge_pence']}p")
    return "\n".join(lines)


def _schedule_lines(charge_facts):
    lines = []
    for tariff, schedule in charge_facts["tariff_schedules"].items():
        windows = "; ".join(
            f"from {w['opens_on']}: "
            + (f"{w['unit_rate_pence']}p per kWh, {w['standing_charge_pence']}p per day" if "unit_rate_pence" in w
               else f"day {w['day_unit_rate_pence']}p, night {w['night_unit_rate_pence']}p, "
                    f"{w['standing_charge_pence']}p per day")
            for w in schedule["price_windows"])
        roll = f"moves to {schedule['rolls_onto']} when the term ends" if schedule["rolls_onto"] else "no fixed term"
        lines.append(f"{tariff} (read from {config.TARIFF_DOCUMENT_BY_TARIFF[tariff]}): {windows}; {roll}")
    return "\n".join(lines)


def _comparison_lines(comparison):
    return (f"Amount billed: GBP {comparison['amount_billed_gbp']}\n"
            f"Corrected charge: GBP {comparison['corrected_charge_gbp']}\n"
            f"Difference: GBP {comparison['difference_gbp']} ({comparison['direction']})\n"
            f"Money at stake: GBP {comparison['money_at_stake_gbp']}\n"
            f"The rebill line is GBP {config.REBILL_THRESHOLD_GBP}; a rebill is warranted: "
            f"{_yes_no(comparison['rebill_warranted'])}")


def _redress_lines(redress):
    if not redress["breached_standards"]:
        return "No guaranteed standard is broken, so no payment is due."
    lines = [f"{item['standard_code']}: GBP {item['payment_gbp']}" for item in redress["breached_standards"]]
    return "\n".join(lines) + f"\nTotal payments due: GBP {redress['redress_gbp']}"


def _usage_lines(usage):
    return ", ".join(f"{key.replace('_', ' ')}: {_yes_no(value) if isinstance(value, bool) else value}"
                     for key, value in usage.items())


def advise_on_tariff_charges(charge_facts, dispute_profile, assessment_plan):
    """State which tariff was owed on which days, at which prices, and whether the bill was right."""
    labels = ["TARIFFS OWED", "BILL CHECK", "STANDARDS"]
    prompt = (
        f"You are the tariff advisor for {config.ORGANISATION_NAME}. State which tariff was owed on which "
        "days, at which prices, and whether the bill was right.\n\n"
        f"THE SCHEDULES\n{_schedule_lines(charge_facts)}\n\n"
        f"THE USAGE, FROM THE VERIFIED READS\n{_usage_lines(charge_facts['usage'])}\n\n"
        f"THE PIECES\n{_piece_lines(charge_facts['pieces'])}\n\n"
        f"THE COMPARISON\n{_comparison_lines(charge_facts['comparison'])}\n\n"
        f"THE STANDARDS BROKEN\n{_redress_lines(charge_facts['redress'])}\n\n"
        f"THE PLAN'S CHECKS\n{assessment_plan['CHECKS']}\n\n"
        "Quote every figure exactly as given. Never recalculate or derive a figure, and never apply one "
        "tariff's prices to another tariff's days. Write several full sentences. Reply in exactly this "
        f"layout:\n{_layout(labels)}")
    fields, record = _ask(prompt, labels, config.AGENT_NAME_TARIFF)
    return {"tariff_advice": fields, "call_record": record}


def write_dispute_assessment(dispute_profile, analyst_request, rebill_facts, charge_facts, effort_facts,
                             rebill_assessment, cause_analysis, tariff_advice):
    """Write the assessment the Revenue Controller decides from, and recommend one outcome."""
    labels = ["ASSESSMENT", "RECOMMENDED DECISION"]
    options = ", ".join(config.DECISION_OPTIONS)
    prompt = (
        f"You are the assessment writer for {config.ORGANISATION_NAME}'s billing disputes desk. You write the "
        "assessment a Revenue Controller decides from. You recommend; you do not decide.\n\n"
        f"THE DISPUTE\n{_facts_block(dispute_profile)}\n\nTHE READS\n{_reads_block(dispute_profile)}\n\n"
        f"WHAT WAS ASKED\n{analyst_request}\n\n"
        f"THE REBILL AGENT\n{_fields_text(rebill_assessment)}\n\n"
        f"THE CAUSE AGENT\n{_fields_text(cause_analysis)}\n\n"
        f"THE TARIFF AGENT\n{_fields_text(tariff_advice)}\n\n"
        f"THE FIGURES THE TOOLS ESTABLISHED\nRebill probability {rebill_facts['rebill_probability']} "
        f"({rebill_facts['rebill_band']})\n{_comparison_lines(charge_facts['comparison'])}\n"
        f"{_redress_lines(charge_facts['redress'])}\n"
        f"Effort: {effort_facts['effort_needed_hours']} hours; a senior billing analyst must work it: "
        f"{_yes_no(effort_facts['senior_review_required'])}\n\n"
        "THE THREE OUTCOMES, IN THE BILLING DISPUTES POLICY'S TERMS\n"
        f"{config.DECISION_UPHOLD_BILL}: the bill stands; nothing is changed, no compensation is paid and "
        f"nothing is settled.\n{config.DECISION_REBILL}: a corrected bill statement is issued for the difference.\n"
        f"{config.DECISION_REBILL_AND_COMPENSATE}: a redress letter goes to the customer and a corrected bill "
        "statement shows the compensation credited. A bill is corrected only when it is out by "
        f"GBP {config.REBILL_THRESHOLD_GBP} or more, either way.\n\n"
        "Say what went wrong only from the facts you are given, and quote every figure exactly. "
        "Write several full sentences. Reply in exactly this layout:\n"
        f"{_layout(labels)}\nRECOMMENDED DECISION must be one of: {options}.")
    fields, record = _ask(prompt, labels, config.AGENT_NAME_WRITER)
    first_line = fields["RECOMMENDED DECISION"].splitlines()[0]
    cleaned = first_line.strip(config.RESPONSE_DECORATION_CHARACTERS + ".").strip().upper()
    if cleaned not in config.DECISION_OPTIONS:
        raise ValueError(f"The {config.AGENT_NAME_WRITER} agent recommended '{first_line}', which is "
                         f"not one of {config.DECISION_OPTIONS}.")
    fields["RECOMMENDED DECISION"] = cleaned
    return {"dispute_assessment": fields, "call_record": record}


def draft_redress_letter(dispute_profile, redress, customer_steps):
    """Write the letter the customer reads at home."""
    labels = ["SUBJECT", "LETTER"]
    prompt = (
        f"You write letters to customers for {config.ORGANISATION_NAME}, following its Billing Disputes "
        "Policy: plain words, short sentences and one apology.\n\n"
        f"Dispute reference: {_value(dispute_profile, config.DISPUTE_REFERENCE_COLUMN)}\n"
        f"The bill covers {_value(dispute_profile, config.BILL_START_COLUMN)} to "
        f"{_value(dispute_profile, config.BILL_END_COLUMN)}; the customer's tariff is "
        f"{_value(dispute_profile, config.ENTITLED_TARIFF_COLUMN)}.\n"
        f"PROMISES BROKEN AND PAYMENTS\n{_redress_lines(redress)}\n\n"
        "THE GUIDE'S STEPS FOR THE CUSTOMER\n" + "\n".join(customer_steps) + "\n\n"
        "Say that a corrected bill statement will follow separately, and quote no amount from it. The only "
        "figures you may quote are the payments you are given. Never name a billing system, a member of "
        "staff or any identifier except the dispute reference, and invent no contact details. Reply in "
        f"exactly this layout:\n{_layout(labels)}\n" + _NO_FIGURES)
    fields, record = _ask(prompt, labels, config.AGENT_NAME_REDRESS_LETTER)
    return {"redress_letter": fields, "call_record": record}


def draft_rebill_statement(dispute_profile, charge_facts, redress_letter, settlement):
    """Write the corrected bill statement, the one place the customer is given the corrected figures."""
    labels = ["PIECES", "TOTALS", "COMPENSATION", "SETTLEMENT"]
    pieces = charge_facts["pieces"]
    numbered = []
    for number, piece in enumerate(pieces, start=1):
        window = piece["price_window"]
        if "unit_rate_pence" in window:
            detail = (f"usage {piece['units_kwh']} kWh at {window['unit_rate_pence']}p per kWh, standing charge "
                      f"{window['standing_charge_pence']}p per day")
        else:
            detail = (f"usage day {piece['day_units_kwh']} kWh at {window['day_unit_rate_pence']}p and night "
                      f"{piece['night_units_kwh']} kWh at {window['night_unit_rate_pence']}p per kWh, standing "
                      f"charge {window['standing_charge_pence']}p per day")
        numbered.append(f"{number}. {piece['first_day']} to {piece['last_day']}, {piece['days']} days, "
                        f"{piece['tariff']}, {detail}, charge {piece['charge_pence']}p")
    comparison = charge_facts["comparison"]
    letter_line = (f"A redress letter was written to the customer, subject: {redress_letter['SUBJECT']}. "
                   f"Compensation credited: GBP {charge_facts['redress']['redress_gbp']}."
                   if redress_letter else "No redress letter was written and no compensation is paid.")
    settled = (f"Settled amount GBP {settlement['settled_amount_gbp']}, {settlement['direction']} "
               f"(amount to settle GBP {settlement['amount_to_settle_gbp']})." if settlement else "Nothing is settled.")
    prompt = (
        f"You write corrected bill statements for {config.ORGANISATION_NAME}. This statement is the one place "
        "the customer is given the corrected bill's figures.\n\n"
        f"Account: {_value(dispute_profile, 'account_number')}; dispute {_value(dispute_profile, config.DISPUTE_REFERENCE_COLUMN)}\n"
        f"The original bill: GBP {comparison['amount_billed_gbp']}, "
        f"{_value(dispute_profile, config.BILL_START_COLUMN)} to {_value(dispute_profile, config.BILL_END_COLUMN)}\n\n"
        "THE PIECES\n" + "\n".join(numbered) + "\n\n"
        f"TOTALS\nCorrected charge GBP {comparison['corrected_charge_gbp']}; difference GBP "
        f"{comparison['difference_gbp']} ({comparison['direction']})\n\n"
        f"COMPENSATION\n{letter_line}\n\nSETTLEMENT\n{settled}\n\n"
        "Show every piece once and in date order. Copy every figure as given, and write each label once. "
        "Write each piece's charge exactly as given, for example 19244.80p. Reply in exactly this layout:\n"
        f"{_layout(labels)}\n" + _NO_FIGURES)
    fields, record = _ask(prompt, labels, config.AGENT_NAME_REBILL_STATEMENT)
    for piece in pieces:
        shown = f"{piece['charge_pence']}p"
        needed = sum(1 for other in pieces if f"{other['charge_pence']}p" == shown)
        if fields["PIECES"].count(shown) < needed:
            raise ValueError(f"The {config.AGENT_NAME_REBILL_STATEMENT} agent's statement does not show the "
                             f"charge {shown} for every piece that carries it.")
    return {"rebill_statement": fields, "call_record": record}
