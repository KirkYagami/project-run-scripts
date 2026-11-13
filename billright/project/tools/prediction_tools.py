"""Turns a model's raw output into the facts the business acts on."""
from collections import Counter

import numpy as np
import pandas as pd

from config import config
from data_pipeline.feature_builder import build_feature_frame


def _band(probability):
    if probability >= config.REBILL_BAND_HIGH_THRESHOLD:
        return config.REBILL_BAND_HIGH
    if probability >= config.REBILL_BAND_MEDIUM_THRESHOLD:
        return config.REBILL_BAND_MEDIUM
    return config.REBILL_BAND_LOW


def build_rebill_facts(rebill_model, rebill_feature_names, disputes):
    """Give each dispute its rebill probability and band."""
    features = build_feature_frame(disputes, config.REBILL_NUMERIC_FEATURES,
                                   config.REBILL_CATEGORICAL_FEATURES)[list(rebill_feature_names)]
    positive = list(rebill_model.classes_).index(1)
    probabilities = rebill_model.predict_proba(features)[:, positive]
    facts = []
    for probability in probabilities:
        rounded = round(float(probability), config.PROBABILITY_DECIMALS)
        facts.append({"rebill_probability": rounded, "rebill_band": _band(rounded)})
    return facts


def build_cause_facts(cause_model, note_texts):
    """Name the category a dispute's notes describe, and say how far they agree."""
    readable = [text for text in note_texts if len(str(text).split()) >= config.MINIMUM_NOTE_WORDS]
    too_short = len(note_texts) - len(readable)
    if not readable:
        raise ValueError("No note is long enough to read: each has fewer than "
                         f"{config.MINIMUM_NOTE_WORDS} words.")
    probabilities = cause_model.predict_proba(readable)
    classes = [str(name) for name in cause_model.classes_]
    note_categories = [classes[int(index)] for index in np.argmax(probabilities, axis=1)]
    counts = Counter(note_categories)
    most = max(counts.values())
    tied = [name for name, count in counts.items() if count == most]
    summed = {name: float(probabilities[:, classes.index(name)].sum()) for name in tied}
    chosen = max(tied, key=lambda name: (summed[name], name))
    others = sorted(name for name in counts if name != chosen)
    return {
        "dispute_category": chosen,
        "agreement": round(counts[chosen] / len(readable), config.PROBABILITY_DECIMALS),
        "notes_read": len(readable),
        "notes_too_short_to_read": too_short,
        "note_categories": note_categories,
        "other_categories": others,
    }


def estimate_resolution_effort(effort_model, effort_feature_names, dispute_profile, rebill_band,
                               dispute_category, charge_pieces, money_at_stake_gbp):
    """Estimate the hours the dispute needs, and whether a senior analyst must work it."""
    source = dispute_profile.get(config.VERIFIED_READ_SOURCE_COLUMN)
    if source not in config.VERIFIED_READ_SOURCES:
        raise ValueError(f"The verified read source '{source}' is not one of "
                         f"{config.VERIFIED_READ_SOURCES}.")
    priority = dispute_profile.get(config.PRIORITY_SERVICES_COLUMN)
    if priority not in (config.BOOLEAN_YES, config.BOOLEAN_NO):
        raise ValueError(f"The Priority Services flag '{priority}' is neither Yes nor No.")

    yes_no = lambda condition: config.BOOLEAN_YES if condition else config.BOOLEAN_NO
    tariffs = {piece["tariff"] for piece in charge_pieces}
    tariffs.add(dispute_profile[config.BILLED_TARIFF_COLUMN])
    assumptions = config.EFFORT_PLANNING_ASSUMPTIONS
    row = {
        "analyst_grade": assumptions["analyst_grade"],
        "billing_centre": dispute_profile.get("billing_centre"),
        "contact_channel": dispute_profile.get("contact_channel"),
        "dispute_category": dispute_category,
        "rebill_band": rebill_band,
        "meter_type": dispute_profile.get("meter_type"),
        "smart_meter_flag": dispute_profile.get("smart_meter_flag"),
        "verified_reads_obtained_flag": config.BOOLEAN_YES,
        "site_visit_required_flag": yes_no(source in config.SITE_VISIT_READ_SOURCES),
        "meter_test_required_flag": yes_no(source in config.METER_TEST_READ_SOURCES),
        "meter_operator_involved_flag": yes_no(source in config.METER_OPERATOR_READ_SOURCES),
        "priority_services_flag": config.BOOLEAN_NO,
        "complaint_escalated_flag": assumptions["complaint_escalated_flag"],
        "bill_pieces_count": len(charge_pieces),
        "tariffs_involved_count": len(tariffs),
        "amount_at_stake_gbp": float(money_at_stake_gbp),
        "letters_sent_count": assumptions["letters_sent_count"],
        "calls_made_count": assumptions["calls_made_count"],
        "analyst_open_disputes_count": assumptions["analyst_open_disputes_count"],
    }
    features = build_feature_frame(pd.DataFrame([row]), config.EFFORT_NUMERIC_FEATURES,
                                   config.EFFORT_CATEGORICAL_FEATURES)[list(effort_feature_names)]
    estimate = float(effort_model.predict(features)[0])
    apply = priority == config.BOOLEAN_YES
    needed = estimate * config.PRIORITY_SERVICES_EFFORT_MULTIPLIER if apply else estimate
    needed = round(needed, config.EFFORT_HOURS_DECIMALS)
    return {
        "base_hours": round(estimate, config.EFFORT_HOURS_DECIMALS),
        "effort_needed_hours": needed,
        "multiplier_applied": bool(apply),
        "senior_review_required": bool(needed > config.SENIOR_REVIEW_THRESHOLD_HOURS),
        "planning_assumptions": dict(config.EFFORT_PLANNING_ASSUMPTIONS),
    }
