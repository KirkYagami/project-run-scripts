"""Explicit opt-in external-model double for offline contract verification.
Never loaded by the application or by the normal supplied pytest command.
"""

from pathlib import Path
import tempfile
from unittest.mock import patch
import pytest
from config import config as c
from verification.model_double import fake


@pytest.fixture(scope="session", autouse=True)
def isolated_external_boundary():
    sandbox = Path(tempfile.mkdtemp(prefix="p7-offline-contracts-"))
    c.APPLICATION_DATABASE_FILE = str(sandbox / "app.db")
    c.APPLICATION_DATABASE_URL = "sqlite:///" + c.APPLICATION_DATABASE_FILE
    c.CHECKPOINT_DATABASE_FILE = str(sandbox / "checkpoint.db")
    from run_database_setup import main

    main()
    from agentic import agents
    from chat import authorisation_assistant

    with patch.object(agents, "call_language_model", side_effect=fake), patch.object(
        authorisation_assistant, "call_language_model", side_effect=fake
    ):
        yield
