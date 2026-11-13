"""Reads prices, roll-overs and payments out of the documents that state them.

This is the only module that knows how a price is written, and it reads each
tariff from its own schedule alone.
"""
import re
from decimal import Decimal

from config import config
from knowledge.vector_index import read_document_chunks


def _opening_day(day_text, month_text):
    month_name = config.MONTH_NAME_MAPPING.get(month_text.strip().lower())
    opens_on = f"{int(day_text):02d} {month_name}" if month_name else None
    if opens_on not in config.DAY_NUMBER_BY_PRICE_YEAR_DATE:
        raise ValueError(f"'{day_text} {month_text}' is not a day of the price year")
    return opens_on


def _read_single_rate_windows(passages):
    windows = {}
    for passage in passages:
        for match in re.finditer(config.SINGLE_RATE_PRICE_PATTERN, passage):
            opens_on = _opening_day(match.group(1), match.group(2))
            windows.setdefault(opens_on, set()).add(
                (Decimal(match.group(3)), Decimal(match.group(4))))
    return windows


def _read_two_rate_windows(passages):
    windows = {}
    for passage in passages:
        for match in re.finditer(config.TWO_RATE_PRICE_PATTERN, passage):
            opens_on = _opening_day(match.group(1), match.group(2))
            windows.setdefault(opens_on, set()).add(
                (Decimal(match.group(3)), Decimal(match.group(4)), Decimal(match.group(5))))
    return windows


def _read_roll_over(passages, document_name):
    roll_overs = set()
    no_fixed_term = False
    for passage in passages:
        for match in re.finditer(config.ROLL_OVER_PATTERN, passage):
            roll_overs.add(match.group(1).strip())
        if re.search(config.NO_FIXED_TERM_PATTERN, passage):
            no_fixed_term = True
    if roll_overs and no_fixed_term:
        raise ValueError(f"{document_name} states both a roll-over and that it has no fixed term")
    if not roll_overs and not no_fixed_term:
        raise ValueError(f"{document_name} states neither a roll-over nor that it has no fixed term")
    if no_fixed_term:
        return None
    if len(roll_overs) > 1:
        raise ValueError(f"{document_name} names two different roll-overs: {sorted(roll_overs)}")
    named = roll_overs.pop()
    tariff = (named if named in config.TARIFF_DOCUMENT_BY_TARIFF
              else config.TARIFF_MAPPING.get(named.lower()))
    if tariff not in config.TARIFF_DOCUMENT_BY_TARIFF:
        raise ValueError(f"{document_name} rolls onto '{named}', which is not one of the five tariffs")
    return tariff


def read_tariff_schedule(collection, tariff_name):
    """Give the corrected bill every price and roll-over it needs, from the tariff's own schedule."""
    document_name = config.TARIFF_DOCUMENT_BY_TARIFF[tariff_name]
    passages = read_document_chunks(collection, document_name)

    single_rate = _read_single_rate_windows(passages)
    two_rate = _read_two_rate_windows(passages)
    if single_rate and two_rate:
        raise ValueError(f"{document_name} states prices in both the single-rate and the "
                         f"two-rate form")
    if not single_rate and not two_rate:
        raise ValueError(f"{document_name} states no prices")

    windows_by_day = single_rate or two_rate
    price_windows = []
    for opens_on in sorted(windows_by_day, key=config.DAY_NUMBER_BY_PRICE_YEAR_DATE.get):
        prices = windows_by_day[opens_on]
        if len(prices) > 1:
            raise ValueError(f"{document_name} states two different prices from {opens_on}")
        price = next(iter(prices))
        if single_rate:
            price_windows.append({"opens_on": opens_on, "unit_rate_pence": price[0],
                                  "standing_charge_pence": price[1]})
        else:
            price_windows.append({"opens_on": opens_on, "day_unit_rate_pence": price[0],
                                  "night_unit_rate_pence": price[1],
                                  "standing_charge_pence": price[2]})
    if price_windows[0]["opens_on"] != config.PRICE_YEAR_DATES[0]:
        raise ValueError(f"{document_name} states no price from {config.PRICE_YEAR_DATES[0]}")

    return {"price_windows": price_windows,
            "rolls_onto": _read_roll_over(passages, document_name)}


def read_standard_payments(collection):
    """Give the redress every guaranteed standard payment, from the standards document alone."""
    passages = read_document_chunks(collection, config.STANDARDS_DOCUMENT)
    payments = {}
    for code, phrase in config.GUARANTEED_STANDARD_BREACH_PHRASES.items():
        found = set()
        for passage in passages:
            for match in re.finditer(config.STANDARD_PAYMENT_PATTERN, passage):
                if phrase.lower() in match.group(1).lower():
                    found.add(Decimal(match.group(2)))
        if not found:
            raise ValueError(f"{config.STANDARDS_DOCUMENT} states no payment for {code}")
        if len(found) > 1:
            raise ValueError(f"{config.STANDARDS_DOCUMENT} states different payments for {code}: "
                             f"{sorted(found)}")
        payments[code] = found.pop()
    return payments
