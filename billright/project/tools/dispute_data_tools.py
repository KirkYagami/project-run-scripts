"""Serves single records out of the live queue.

Every function works on tables its caller has already loaded; none reads a file and none
changes the data it is given.
"""
import pandas as pd

from config import config


def _is_gap(value):
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def fetch_dispute_profile(open_disputes, dispute_reference):
    """Give one dispute's own facts to whatever is about to reason about it."""
    rows = open_disputes[open_disputes[config.DISPUTE_REFERENCE_COLUMN] == dispute_reference]
    if len(rows) == 0:
        raise ValueError(config.DISPUTE_NOT_IN_QUEUE_MESSAGE.format(dispute_reference=dispute_reference))
    if len(rows) > 1:
        raise ValueError(f"Dispute {dispute_reference} is in the open queue {len(rows)} times, "
                         f"so its facts cannot be told apart.")
    return rows.iloc[0].to_dict()


def fetch_dispute_notes(open_dispute_notes, dispute_reference):
    """Hand the cause model one dispute's notes, oldest first."""
    rows = open_dispute_notes[open_dispute_notes[config.DISPUTE_REFERENCE_COLUMN] == dispute_reference]
    if len(rows) == 0:
        raise ValueError(config.DISPUTE_WITHOUT_NOTES_MESSAGE.format(dispute_reference=dispute_reference))
    sequences = []
    for value in rows[config.NOTE_SEQUENCE_COLUMN]:
        if _is_gap(value):
            raise ValueError(f"A note of {dispute_reference} carries no {config.NOTE_SEQUENCE_COLUMN}.")
        try:
            sequences.append(int(float(str(value).strip())))
        except ValueError:
            raise ValueError(f"A note of {dispute_reference} has the sequence '{value}', "
                             f"which is not a number.")
    if len(set(sequences)) != len(sequences):
        raise ValueError(f"The notes of {dispute_reference} do not each carry their own sequence number.")
    ordered = rows.assign(_sequence=sequences).sort_values("_sequence", kind="stable")
    return [str(text) for text in ordered[config.NOTE_TEXT_COLUMN]]
