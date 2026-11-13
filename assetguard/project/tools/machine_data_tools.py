"""Factual lookups about one machine from the live fleet and the note history.

Nothing here predicts or calls a language model, so the same tag always gives
the same answer.
"""

from data_pipeline.dataset_loader import load_processed_dataset


def _plain_value(value):
    """Turn numpy scalars into plain Python values so records serialise cleanly."""
    return value.item() if hasattr(value, "item") else value


def load_current_fleet(fleet_file_path):
    """The live fleet, one row per machine, typed like any cleaned file."""
    return load_processed_dataset(fleet_file_path)


def fetch_machine_profile(fleet_frame, machine_code):
    """One machine's current row as a flat record, or {} for an unknown tag."""
    matches = fleet_frame[fleet_frame["machine_code"] == machine_code]
    if len(matches) == 0:
        return {}
    return {column_name: _plain_value(value) for column_name, value in matches.iloc[0].items()}


def fetch_machine_note_history(notes_frame, machine_code):
    """Every note text for one machine, oldest first, or [] when it has none."""
    machine_notes = notes_frame[notes_frame["machine_code"] == machine_code]
    machine_notes = machine_notes.sort_values("note_date", kind="stable")
    return [str(note_text) for note_text in machine_notes["note_text"]]
