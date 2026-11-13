"""The six agents, plus the shared machinery for one language model call.

Every agent is exactly one model call: facts arrive as arguments, a judgement in
words leaves as the return value. No agent can call a tool, fetch data, score
risk, set a priority, estimate a duration or search the manuals.
"""

import json
import os
import re
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

from config import config

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

_api_key = os.getenv(config.GEMINI_API_KEY_VARIABLE, "").strip()
if not _api_key or _api_key.lower().startswith(("your", "test", "replace", "<")):
    raise RuntimeError(
        config.GEMINI_API_KEY_VARIABLE + " is missing or still a placeholder. Put a real Gemini "
        "API key in Project/.env before starting the service."
    )

# The SDK retries failed requests by itself unless told not to. One invocation
# must be exactly one call, so a failure surfaces instead of silently repeating.
_client = genai.Client(
    api_key=_api_key,
    http_options=types.HttpOptions(retry_options=types.HttpRetryOptions(attempts=1)),
)
_generation_settings = types.GenerateContentConfig(
    temperature=config.GEMINI_TEMPERATURE,
    max_output_tokens=config.GEMINI_MAX_OUTPUT_TOKENS,
    # Agents interpret facts they are given; they never reach out for more.
    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
)

LABEL_DECORATION = r"^[\s\-\*#•>]*"
LIST_MARKER = re.compile(r"^\s*(?:\d+\s*[.):-]|[-*•#]+)\s*")
SECTION_LINE = re.compile(r"^[\s#*]*[A-Za-z][A-Za-z0-9 /&()'-]{0,40}\s*\**\s*:")

# Field labels each agent asks the model to use, and the dictionary key each becomes.
PLANNER_FIELDS = ["INVESTIGATION FOCUS", "ORDER OF CHECKS", "RATIONALE"]
CONDITION_FIELDS = ["CONDITION SUMMARY", "KEY SIGNALS", "URGENCY", "RECOMMENDATION"]
PROBLEM_FIELDS = ["LIKELY PROBLEM TYPE", "CONFIDENCE COMMENT", "SUPPORTING EVIDENCE"]
PROCEDURE_FIELDS = ["PROCEDURE REFERENCE", "PERMIT REQUIRED", "PARTS REQUIRED", "SAFETY NOTES"]
PROCEDURE_STEPS_LABEL = "KEY STEPS"
WRITER_FIELDS = ["JOB SUMMARY", "SCHEDULING NOTE"]
WRITER_STEPS_LABEL = "TASK STEPS"
FINALIZER_FIELDS = ["FINAL SUMMARY", "CHANGES APPLIED"]
FINALIZER_STEPS_LABEL = "TASK STEPS"

FORMAT_RULES = (
    "Answer using exactly the labelled lines below, in this order. Put each value on the "
    "same line as its label, keep it to one line, and write nothing before or after them."
)


def _field_key(label):
    return label.lower().replace(" ", "_")


def _keyed(parsed_fields):
    return {_field_key(label): value for label, value in parsed_fields.items()}


def _facts_block(facts):
    return json.dumps(facts, indent=2, default=str)


def call_language_model(prompt_text, agent_name):
    """Exactly one call to the configured model; returns the tidied reply and its cost."""
    started = time.perf_counter()
    response = _client.models.generate_content(
        model=config.GEMINI_MODEL_NAME, contents=prompt_text, config=_generation_settings)
    latency_milliseconds = int(round((time.perf_counter() - started) * 1000))
    response_text = (response.text or "").strip()
    return {
        "response_text": response_text,
        "call_record": {
            "agent_name": agent_name,
            "model_name": config.GEMINI_MODEL_NAME,
            "prompt_characters": len(prompt_text),
            "response_characters": len(response_text),
            "latency_milliseconds": latency_milliseconds,
        },
    }


def parse_labelled_response(response_text, field_labels):
    """{label: value} for each requested label; the latest occurrence wins, missing ones are ''."""
    parsed = {label: "" for label in field_labels}
    for line in response_text.splitlines():
        cleaned = re.sub(LABEL_DECORATION, "", line).replace("**", "")
        for label in field_labels:
            match = re.match(r"^\s*" + re.escape(label) + r"\s*:\s*(.*)$", cleaned, flags=re.IGNORECASE)
            if match:
                parsed[label] = match.group(1).strip()
    return parsed


def parse_numbered_steps(response_text, section_label):
    """The list items under section_label, without markers, stopping at the next labelled section."""
    lines = response_text.splitlines()
    heading = re.compile(r"^\s*" + re.escape(section_label) + r"\s*:?\s*(.*)$", flags=re.IGNORECASE)
    steps = []
    collecting = False
    for line in lines:
        cleaned = re.sub(LABEL_DECORATION, "", line).replace("**", "")
        if not collecting:
            match = heading.match(cleaned)
            if match:
                collecting = True
                if match.group(1).strip():
                    steps.append(LIST_MARKER.sub("", match.group(1)).strip())
            continue
        if not line.strip():
            continue
        if not LIST_MARKER.match(line) and SECTION_LINE.match(line):
            break
        step = LIST_MARKER.sub("", line).replace("**", "").strip()
        if step:
            steps.append(step)
    return steps


def _labelled_template(field_labels, steps_label=None, steps_after=None):
    lines = []
    for label in field_labels:
        lines.append(label + ": <one line>")
        if steps_label and label == steps_after:
            lines.append(steps_label + ":")
            lines.append("1. <step>")
            lines.append("2. <step>")
    if steps_label and steps_after is None:
        lines.append(steps_label + ":")
        lines.append("1. <step>")
        lines.append("2. <step>")
    return "\n".join(lines)


def work_planner_agent(machine_profile, request_text):
    """The supervising agent: decide what the specialists should look at, and in what order."""
    register_facts = {
        name: machine_profile.get(name)
        for name in ("machine_code", "machine_type", "factory_name", "production_line",
                     "importance", "usage_pattern", "machine_age_months")
    }
    prompt_text = (
        "You lead a maintenance reliability team at Meridian Heavy Industries. A reliability "
        "engineer has asked for a repair job assessment on one machine. Decide what the "
        "specialist team should concentrate on and in what order they should check it.\n\n"
        "You are given only the machine's register record. Do not diagnose anything, do not "
        "invent condition readings, and do not estimate risk or priority; the specialists and "
        "the plant's models do that.\n\n"
        "Machine register record:\n" + _facts_block(register_facts) + "\n\n"
        "Engineer's request: " + request_text + "\n\n"
        + FORMAT_RULES + "\n" + _labelled_template(PLANNER_FIELDS)
    )
    reply = call_language_model(prompt_text, config.AGENT_NAME_PLANNER)
    result = _keyed(parse_labelled_response(reply["response_text"], PLANNER_FIELDS))
    result["call_record"] = reply["call_record"]
    return result


def condition_analyst_agent(machine_profile, risk_facts, investigation_plan):
    """Explain what this week's readings and the model's settled risk score mean."""
    condition_readings = {
        name: machine_profile.get(name)
        for name in ("machine_code", "machine_type", "power_rating_kw", "average_vibration",
                     "highest_vibration", "vibration_change_pct", "average_temperature_c",
                     "highest_temperature_c", "room_temperature_c", "oil_dirtiness_score",
                     "days_since_oil_check", "alarms_this_week", "days_since_last_service",
                     "breakdowns_last_year", "running_hours_per_week", "average_load_pct")
    }
    plan = {name: value for name, value in investigation_plan.items() if name != "call_record"}
    prompt_text = (
        "You are the condition analyst on a maintenance reliability team. Explain to a "
        "maintenance supervisor what this week's condition readings and the breakdown risk "
        "model's score mean for this machine.\n\n"
        "The breakdown probability and risk band below are settled facts produced by the "
        "plant's trained model. Do not recalculate, adjust or question them. Cite only the "
        "readings listed here; do not invent any.\n\n"
        "Team lead's brief (answer it):\n" + _facts_block(plan) + "\n\n"
        "Risk facts:\n" + _facts_block({
            "breakdown_probability": risk_facts["breakdown_probability"],
            "risk_band": risk_facts["risk_band"],
        }) + "\n\n"
        "This week's readings:\n" + _facts_block(condition_readings) + "\n\n"
        "URGENCY is one plain word for a human reader (for example Immediate, Soon or Routine). "
        "It is not the repair job priority, which is set separately by plant policy.\n\n"
        + FORMAT_RULES + "\n" + _labelled_template(CONDITION_FIELDS)
    )
    reply = call_language_model(prompt_text, config.AGENT_NAME_CONDITION)
    result = _keyed(parse_labelled_response(reply["response_text"], CONDITION_FIELDS))
    result["call_record"] = reply["call_record"]
    return result


def problem_analyst_agent(problem_facts, condition_assessment):
    """Weigh the note classifier's votes against the condition reading."""
    assessment = {name: value for name, value in condition_assessment.items() if name != "call_record"}
    prompt_text = (
        "You are the reliability engineer on a maintenance team. A trained classifier has read "
        "every past technician note for this machine and voted on the problem type each note "
        "describes. Judge what those votes mean and whether the condition data supports or "
        "contradicts them.\n\n"
        "Do not reclassify the notes yourself. LIKELY PROBLEM TYPE must be one of the problem "
        "types that appear in the vote count below, written exactly as it appears there. If "
        "there are no votes, write None.\n\n"
        "Classifier verdict on the note history:\n" + _facts_block(problem_facts) + "\n\n"
        "Condition analyst's reading:\n" + _facts_block(assessment) + "\n\n"
        + FORMAT_RULES + "\n" + _labelled_template(PROBLEM_FIELDS)
    )
    reply = call_language_model(prompt_text, config.AGENT_NAME_PROBLEM)
    result = _keyed(parse_labelled_response(reply["response_text"], PROBLEM_FIELDS))
    result["call_record"] = reply["call_record"]
    return result


def procedure_advisor_agent(procedure_facts, problem_analysis):
    """Turn the retrieved manual and safety passages into the procedure part of a repair job."""
    analysis = {name: value for name, value in problem_analysis.items() if name != "call_record"}
    prompt_text = (
        "You are the procedure specialist on a maintenance team. Using ONLY the manual passages "
        "below, state which procedure applies, the permit position, the parts named, the safety "
        "requirements, and the repair steps in order.\n\n"
        "Every detail must come from the passages. Where a detail is not in them, write "
        "'Not stated in the retrieved documents' rather than supplying it from general "
        "engineering knowledge. Quote procedure codes, part codes and torque values exactly.\n\n"
        "Reliability engineer's judgement:\n" + _facts_block(analysis) + "\n\n"
        "Repair procedure passages:\n" + procedure_facts["procedure_context"] + "\n\n"
        "Safety passages:\n" + procedure_facts["safety_context"] + "\n\n"
        + FORMAT_RULES + " List the steps under " + PROCEDURE_STEPS_LABEL + " as a numbered list, "
        "one step per line.\n" + _labelled_template(PROCEDURE_FIELDS, PROCEDURE_STEPS_LABEL)
    )
    reply = call_language_model(prompt_text, config.AGENT_NAME_PROCEDURE)
    result = _keyed(parse_labelled_response(reply["response_text"], PROCEDURE_FIELDS))
    result["key_steps"] = parse_numbered_steps(reply["response_text"], PROCEDURE_STEPS_LABEL)
    result["call_record"] = reply["call_record"]
    return result


def repair_job_writer_agent(condition_assessment, problem_analysis, procedure_guidance):
    """Write the draft a supervisor will read: summary, task steps and a scheduling note."""
    def without_call(record):
        return {name: value for name, value in record.items() if name != "call_record"}

    prompt_text = (
        "You write repair jobs for Meridian Heavy Industries. Write a DRAFT repair job that a "
        "maintenance supervisor must approve before any work starts.\n\n"
        "Use only the steps the procedure specialist provided; you may tidy their wording but "
        "must not add a step they did not give. Do not state or work out a risk number, a "
        "priority or a downtime estimate; those are set elsewhere. JOB SUMMARY is two sentences "
        "a supervisor can read at a glance. SCHEDULING NOTE says when the work should be done "
        "and why, in one line.\n\n"
        "Condition analyst:\n" + _facts_block(without_call(condition_assessment)) + "\n\n"
        "Reliability engineer:\n" + _facts_block(without_call(problem_analysis)) + "\n\n"
        "Procedure specialist:\n" + _facts_block(without_call(procedure_guidance)) + "\n\n"
        + FORMAT_RULES + " List the steps under " + WRITER_STEPS_LABEL + " as a numbered list, "
        "one step per line.\n" + _labelled_template(WRITER_FIELDS, WRITER_STEPS_LABEL, "JOB SUMMARY")
    )
    reply = call_language_model(prompt_text, config.AGENT_NAME_WRITER)
    result = _keyed(parse_labelled_response(reply["response_text"], WRITER_FIELDS))
    result["task_steps"] = parse_numbered_steps(reply["response_text"], WRITER_STEPS_LABEL)
    result["call_record"] = reply["call_record"]
    return result


def repair_job_finalizer_agent(draft_repair_job, review_decision):
    """Rewrite the draft to carry out exactly what the supervisor decided, and say what changed."""
    draft_view = {
        name: draft_repair_job.get(name)
        for name in ("job_summary", "task_steps", "scheduling_note", "proposed_window")
    }
    prompt_text = (
        "You finalise repair jobs after a maintenance supervisor's review. Rewrite the draft so "
        "it carries out exactly what the supervisor decided.\n\n"
        "Apply the supervisor's instruction exactly: add no work they did not ask for and drop "
        "nothing they did not ask to remove. If the instruction asks for no change, keep the "
        "summary and steps as they are and write 'No changes' under CHANGES APPLIED.\n\n"
        "Draft repair job:\n" + _facts_block(draft_view) + "\n\n"
        "Supervisor's decision:\n" + _facts_block({
            "decision": review_decision.get("decision"),
            "reviewer_name": review_decision.get("reviewer_name"),
            "feedback_text": review_decision.get("feedback_text"),
        }) + "\n\n"
        + FORMAT_RULES + " List the steps under " + FINALIZER_STEPS_LABEL + " as a numbered list, "
        "one step per line.\n" + _labelled_template(FINALIZER_FIELDS, FINALIZER_STEPS_LABEL, "FINAL SUMMARY")
    )
    reply = call_language_model(prompt_text, config.AGENT_NAME_FINALIZER)
    result = _keyed(parse_labelled_response(reply["response_text"], FINALIZER_FIELDS))
    result["task_steps"] = parse_numbered_steps(reply["response_text"], FINALIZER_STEPS_LABEL)
    result["call_record"] = reply["call_record"]
    return result
