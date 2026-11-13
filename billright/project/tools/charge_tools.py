"""Rebuilds the bill: usage, pieces, corrected charge, comparison, redress, settlement, ranking.

Every figure here is exact and every amount of money is a decimal.Decimal. Pieces are worked
in exact fractions of a penny and rounded only once, at the total.
"""
import math
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction

import pandas as pd

from config import config


# ------------------------------------------------------------------ helpers
def _is_gap(value):
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def _whole(profile, column):
    value = profile.get(column)
    if _is_gap(value):
        raise ValueError(f"The dispute carries no {column}.")
    try:
        number = float(str(value).strip())
    except ValueError:
        raise ValueError(f"{column} is '{value}', which is not a whole number.")
    if number != int(number):
        raise ValueError(f"{column} is '{value}', which is not a whole number.")
    return int(number)


def _fraction(value):
    return Fraction(str(value))


def _decimal_places(value, places):
    return Decimal(value).quantize(Decimal(places), rounding=ROUND_HALF_UP)


def _round_half_up(fraction):
    """Round a non-negative or negative exact fraction to a whole number, half away from zero."""
    sign = -1 if fraction < 0 else 1
    return sign * math.floor(abs(fraction) + Fraction(1, 2))


def _fraction_to_quantum(fraction, quantum):
    """An exact fraction as a Decimal at the quantum, rounded half up."""
    step = Fraction(quantum)
    steps = _round_half_up(fraction / step)
    return (Decimal(steps) * Decimal(quantum)).quantize(Decimal(quantum))


def _read_register(profile, opening_column, closing_column, digits):
    opening = _whole(profile, opening_column)
    closing = _whole(profile, closing_column)
    largest = config.REGISTER_NUMBER_BASE ** digits
    for name, read in ((opening_column, opening), (closing_column, closing)):
        if read < 0 or read >= largest:
            raise ValueError(f"{name} {read} could not come from a register of {digits} digits.")
    rolled = closing < opening
    return (closing - opening + (largest if rolled else 0)), rolled


# ------------------------------------------------------------------ usage
def measure_usage(dispute_profile):
    """Measure what the customer used from the reads the investigation verified."""
    meter_type = dispute_profile.get(config.METER_TYPE_COLUMN)
    if meter_type not in (config.SINGLE_RATE_METER_TYPE, config.TWO_RATE_METER_TYPE):
        raise ValueError(f"The meter type '{meter_type}' is neither "
                         f"{config.SINGLE_RATE_METER_TYPE} nor {config.TWO_RATE_METER_TYPE}.")
    digits = _whole(dispute_profile, config.REGISTER_DIGITS_COLUMN)
    day_units, day_rolled = _read_register(dispute_profile, config.VERIFIED_OPENING_READ_COLUMN,
                                           config.VERIFIED_CLOSING_READ_COLUMN, digits)
    if meter_type == config.SINGLE_RATE_METER_TYPE:
        return {"total_units": int(day_units), "register_rolled_over": bool(day_rolled)}
    night_units, night_rolled = _read_register(dispute_profile, config.VERIFIED_NIGHT_OPENING_READ_COLUMN,
                                               config.VERIFIED_NIGHT_CLOSING_READ_COLUMN, digits)
    return {"day_units": int(day_units), "night_units": int(night_units),
            "total_units": int(day_units + night_units),
            "day_register_rolled_over": bool(day_rolled),
            "night_register_rolled_over": bool(night_rolled)}


# ------------------------------------------------------------------ pieces
def _day_number(text, name):
    if _is_gap(text) or str(text).strip() not in config.DAY_NUMBER_BY_PRICE_YEAR_DATE:
        raise ValueError(f"{name} '{text}' is not a day of the price year.")
    return config.DAY_NUMBER_BY_PRICE_YEAR_DATE[str(text).strip()]


def _window_in_force(schedule, day):
    in_force = None
    for window in schedule["price_windows"]:
        if config.DAY_NUMBER_BY_PRICE_YEAR_DATE[window["opens_on"]] <= day:
            in_force = window
    if in_force is None:
        raise ValueError("A schedule has no price window in force on " +
                         config.PRICE_YEAR_DATE_BY_DAY_NUMBER[day] + ".")
    return in_force


def build_charge_pieces(dispute_profile, tariff_schedules):
    """Split the bill wherever what the customer owed changes."""
    first = _day_number(dispute_profile.get(config.BILL_START_COLUMN), config.BILL_START_COLUMN)
    last = _day_number(dispute_profile.get(config.BILL_END_COLUMN), config.BILL_END_COLUMN)
    if last < first:
        raise ValueError("The bill ends before it starts in the price year.")
    entitled = dispute_profile.get(config.ENTITLED_TARIFF_COLUMN)
    term_text = dispute_profile.get(config.FIXED_TERM_LAST_DAY_COLUMN)
    owed_after_term, term_last_day = None, None
    if not _is_gap(term_text):
        term_last_day = _day_number(term_text, config.FIXED_TERM_LAST_DAY_COLUMN)
        rolls_onto = tariff_schedules[entitled]["rolls_onto"]
        if rolls_onto is None:
            raise ValueError(f"A term's last day is recorded against {entitled}, whose schedule "
                             f"says it has no fixed term.")
        if term_last_day < first:
            raise ValueError("The fixed term ended before the bill's first day.")
        owed_after_term = rolls_onto

    pieces = []
    for day in range(first, last + 1):
        tariff = entitled
        if owed_after_term is not None and first <= term_last_day < last and day > term_last_day:
            tariff = owed_after_term
        window = _window_in_force(tariff_schedules[tariff], day)
        label = config.PRICE_YEAR_DATE_BY_DAY_NUMBER[day]
        if pieces and pieces[-1]["tariff"] == tariff and pieces[-1]["price_window"] is window:
            pieces[-1]["last_day"] = label
            pieces[-1]["days"] += 1
        else:
            pieces.append({"tariff": tariff, "first_day": label, "last_day": label, "days": 1,
                           "price_window": window})
    return pieces


# ------------------------------------------------------------------ charge
def compute_corrected_charge(charge_pieces, usage):
    """Charge each piece at its own prices and give the corrected charge."""
    bill_days = sum(piece["days"] for piece in charge_pieces)
    priced, exact_total = [], Fraction(0)
    for piece in charge_pieces:
        window, days = piece["price_window"], piece["days"]
        share = Fraction(days, bill_days)
        standing = days * _fraction(window["standing_charge_pence"])
        out = dict(piece)
        if "unit_rate_pence" in window:
            units = share * usage["total_units"]
            charge = standing + units * _fraction(window["unit_rate_pence"])
            out["units_kwh"] = _fraction_to_quantum(units, config.PIECE_DISPLAY_QUANTUM)
        else:
            if "day_units" not in usage:
                raise ValueError("A two-rate window needs the day and the night usage of a "
                                 "two-rate meter.")
            day_units, night_units = share * usage["day_units"], share * usage["night_units"]
            charge = (standing + day_units * _fraction(window["day_unit_rate_pence"])
                      + night_units * _fraction(window["night_unit_rate_pence"]))
            out["day_units_kwh"] = _fraction_to_quantum(day_units, config.PIECE_DISPLAY_QUANTUM)
            out["night_units_kwh"] = _fraction_to_quantum(night_units, config.PIECE_DISPLAY_QUANTUM)
        out["charge_pence"] = _fraction_to_quantum(charge, config.PIECE_DISPLAY_QUANTUM)
        exact_total += charge
        priced.append(out)
    corrected = _fraction_to_quantum(exact_total / config.PENCE_PER_POUND, config.PENNY)
    return {"pieces": priced, "corrected_charge_gbp": corrected}


# ------------------------------------------------------------------ comparison
def _exact_pounds(value, name):
    if isinstance(value, float) or isinstance(value, bool):
        raise ValueError(f"{name} {value!r} is a floating-point number, not exact pounds and pence.")
    if _is_gap(value):
        raise ValueError(f"The dispute carries no {name}.")
    text = str(value).strip()
    try:
        amount = Decimal(text)
    except Exception:
        raise ValueError(f"{name} '{text}' is not an amount of money.")
    if amount.as_tuple().exponent != -2:
        raise ValueError(f"{name} '{text}' is not written to the penny.")
    return amount


def compare_with_billed(dispute_profile, corrected_charge_gbp):
    """Say whether the bill was right, which way it was wrong, and whether it must be corrected."""
    billed = _exact_pounds(dispute_profile.get(config.AMOUNT_BILLED_COLUMN), config.AMOUNT_BILLED_COLUMN)
    difference = billed - corrected_charge_gbp
    at_stake = abs(difference)
    if difference > 0:
        direction = config.OVERCHARGED
    elif difference < 0:
        direction = config.UNDERCHARGED
    else:
        direction = config.BILLED_CORRECTLY
    return {
        "amount_billed_gbp": billed,
        "corrected_charge_gbp": corrected_charge_gbp,
        "difference_gbp": difference,
        "money_at_stake_gbp": at_stake,
        "direction": direction,
        "rebill_warranted": bool(at_stake >= Decimal(config.REBILL_THRESHOLD_GBP)),
    }


# ------------------------------------------------------------------ redress, settlement, queue
def compute_redress(dispute_profile, standard_payments):
    """Work out the guaranteed standard payments due on the dispute."""
    breached, total = [], Decimal("0.00")
    for code, column in config.GUARANTEED_STANDARD_BREACH_COLUMNS.items():
        flag = dispute_profile.get(column)
        if flag not in (config.BOOLEAN_YES, config.BOOLEAN_NO):
            raise ValueError(f"{column} reads '{flag}', which is neither Yes nor No.")
        if flag == config.BOOLEAN_YES:
            payment = standard_payments[code]
            breached.append({"standard_code": code, "payment_gbp": payment})
            total += payment
    return {"breached_standards": breached, "redress_gbp": total.quantize(Decimal(config.PENNY))}


def compute_settled_amount(decision, difference_gbp, redress_gbp):
    """Work out what a decision settles, the moment the decision arrives."""
    if decision not in config.DECISION_OPTIONS:
        raise ValueError(f"The decision '{decision}' is not one of {config.DECISION_OPTIONS}.")
    for name, amount in (("difference_gbp", difference_gbp), ("redress_gbp", redress_gbp)):
        if not isinstance(amount, Decimal):
            raise ValueError(f"{name} is a {type(amount).__name__}, not a decimal.Decimal.")
    if decision == config.DECISION_UPHOLD_BILL:
        return None
    settled = difference_gbp
    if decision == config.DECISION_REBILL_AND_COMPENSATE:
        settled = difference_gbp + redress_gbp
    if settled > 0:
        direction = config.SETTLEMENT_CREDITED
    elif settled < 0:
        direction = config.SETTLEMENT_PAYABLE
    else:
        direction = config.SETTLEMENT_NOTHING_DUE
    return {"settled_amount_gbp": settled, "amount_to_settle_gbp": abs(settled), "direction": direction}


def rank_dispute_queue(open_disputes, tariff_schedules):
    """Put the dispute with the most money at stake at the top of the desk's list."""
    ranked = []
    for profile in open_disputes.to_dict("records"):
        usage = measure_usage(profile)
        pieces = build_charge_pieces(profile, tariff_schedules)
        corrected = compute_corrected_charge(pieces, usage)["corrected_charge_gbp"]
        row = {key: profile[key] for key in (config.DISPUTE_REFERENCE_COLUMN, config.BILLING_CENTRE_COLUMN,
                                              config.BILLED_TARIFF_COLUMN, config.ENTITLED_TARIFF_COLUMN)}
        row.update(compare_with_billed(profile, corrected))
        ranked.append(row)
    ranked.sort(key=lambda row: (-row["money_at_stake_gbp"], row[config.DISPUTE_REFERENCE_COLUMN]))
    return ranked
