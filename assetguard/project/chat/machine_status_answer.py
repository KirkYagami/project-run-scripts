"""Answers about one machine's condition, written from fleet data rather than the manuals.

No language model is called here. One machine at a time, so a role without the
Fleet overview page cannot rebuild the fleet one question after another.
"""

from config import config


def build_machine_status_answer(machine_profile, risk_facts):
    """The machine, its 30 day risk and its latest readings, in three short blocks."""
    identity = (
        "Machine " + str(machine_profile["machine_code"]) + " is a " + str(machine_profile["machine_type"])
        + " at " + str(machine_profile["factory_name"])
        + ", importance " + str(machine_profile["importance"]) + "."
    )
    risk = (
        "Chance of a breakdown in the next 30 days: " + str(risk_facts["breakdown_probability"])
        + ". Risk band: " + str(risk_facts["risk_band"])
        + ". Repair priority: " + str(risk_facts["priority"]) + "."
    )
    readings = "\n".join([
        "Latest readings:",
        "- Average vibration: " + str(machine_profile["average_vibration"]) + " mm/s",
        "- Average temperature: " + str(machine_profile["average_temperature_c"]) + " °C",
        "- Oil dirtiness score: " + str(machine_profile["oil_dirtiness_score"]),
        "- Alarms this week: " + str(machine_profile["alarms_this_week"]),
        "- Days since last service: " + str(machine_profile["days_since_last_service"]),
    ])
    return identity + "\n\n" + risk + "\n\n" + readings


def build_unknown_machine_answer(machine_code):
    """Ask which machine is meant, or say the code that was tried is not in the fleet."""
    if not machine_code:
        return (
            "Which machine do you mean? Name it by its machine code, for example PMP-CHE-0067, "
            "and I will look up its condition."
        )
    return config.CHAT_UNKNOWN_MACHINE_MESSAGE + " Code tried: " + machine_code
