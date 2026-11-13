"""Runs the three trained models and applies the written business rules.

Every answer here is a number or a table lookup, produced the same way every
time. Agents explain these answers; they never work them out or overrule them.
"""

import pandas as pd

from config import config

# The machine profile fields a planned repair job copies under the same name.
PROFILE_FIELDS_COPIED = [
    "machine_type", "manufacturer", "factory_name", "production_line",
    "importance", "usage_pattern", "power_rating_kw", "machine_age_months",
]


def build_model_input_row(record_dictionary, feature_names):
    """A one-row table holding exactly the schema columns, in schema order."""
    missing = [name for name in feature_names if name not in record_dictionary]
    if missing:
        raise KeyError("The record is missing model features: " + ", ".join(missing))
    return pd.DataFrame([{name: record_dictionary[name] for name in feature_names}], columns=list(feature_names))


def predict_breakdown_probability(breakdown_model, feature_row):
    """P(breakdown) for one row, rounded to 4 decimal places."""
    breakdown_column = list(breakdown_model.classes_).index(1)
    probability = breakdown_model.predict_proba(feature_row)[0][breakdown_column]
    return round(float(probability), 4)


def classify_risk_band(breakdown_probability, risk_thresholds):
    """HIGH at or above the high cut-off, MEDIUM at or above the medium one, otherwise LOW."""
    if breakdown_probability >= risk_thresholds["high"]:
        return config.RISK_BAND_HIGH
    if breakdown_probability >= risk_thresholds["medium"]:
        return config.RISK_BAND_MEDIUM
    return config.RISK_BAND_LOW


def resolve_repair_priority(importance, risk_band):
    """The Policy 01 priority for this importance and band, read from the matrix."""
    matrix_key = (importance, risk_band)
    if matrix_key not in config.PRIORITY_MATRIX:
        raise KeyError("The priority matrix has no entry for " + str(matrix_key))
    return config.PRIORITY_MATRIX[matrix_key]


def detect_problem_type(problem_type_model, text_vectorizer, note_history):
    """Classify every note and report the mode the notes vote for most often."""
    if len(note_history) == 0:
        return {"problem_type": "", "confidence": 0.0, "note_count": 0, "problem_votes": {}}

    predictions = problem_type_model.predict(text_vectorizer.transform(note_history))
    # A dict keeps first-seen order, so on a tie max() returns the mode that
    # appeared earliest in the history.
    problem_votes = {}
    for predicted in predictions:
        label = str(predicted)
        problem_votes[label] = problem_votes.get(label, 0) + 1
    problem_type = max(problem_votes, key=problem_votes.get)
    return {
        "problem_type": problem_type,
        "confidence": round(problem_votes[problem_type] / len(note_history), 4),
        "note_count": len(note_history),
        "problem_votes": problem_votes,
    }


def score_current_fleet(breakdown_model, fleet_frame, feature_names):
    """The fleet with probability, band and priority added, worst first, in one scoring pass."""
    breakdown_column = list(breakdown_model.classes_).index(1)
    probabilities = breakdown_model.predict_proba(fleet_frame[list(feature_names)])[:, breakdown_column]
    thresholds = {"high": config.HIGH_RISK_THRESHOLD, "medium": config.MEDIUM_RISK_THRESHOLD}

    scored = fleet_frame.copy()
    scored["breakdown_probability"] = [round(float(value), 4) for value in probabilities]
    scored["risk_band"] = [classify_risk_band(value, thresholds) for value in scored["breakdown_probability"]]
    scored["priority"] = [
        resolve_repair_priority(importance, band)
        for importance, band in zip(scored["importance"], scored["risk_band"])
    ]
    return scored.sort_values("breakdown_probability", ascending=False, kind="stable").reset_index(drop=True)


def build_planned_repair_record(machine_profile, risk_facts, job_context):
    """Describe a repair that has not happened yet in the shape the downtime model expects.

    Every value is read with [] so a missing field stops the run instead of
    producing a partly filled job.
    """
    planned_record = dict(config.REPAIR_JOB_PLANNING_ASSUMPTIONS)
    for field_name in PROFILE_FIELDS_COPIED:
        planned_record[field_name] = machine_profile[field_name]
    planned_record["repairs_last_year"] = machine_profile["breakdowns_last_year"]
    planned_record["problem_type"] = job_context["problem_type"]
    planned_record["access_level"] = job_context["access_level"]
    planned_record["priority"] = risk_facts["priority"]
    planned_record["severity"] = config.SEVERITY_BY_RISK_BAND[risk_facts["risk_band"]]
    return planned_record


def estimate_repair_downtime(downtime_model, feature_row):
    """The model's own estimate in hours, rounded to 2 places, before any tight space allowance."""
    return round(float(downtime_model.predict(feature_row)[0]), 2)


def apply_tight_space_factor(estimated_hours, access_level):
    """Stretch the estimate by the Safety Rule 03 factor for tight space work only."""
    if access_level == config.ACCESS_LEVEL_TIGHT_SPACE:
        return round(estimated_hours * config.TIGHT_SPACE_DURATION_FACTOR, 2)
    return round(estimated_hours, 2)
