"""Run the supplied suite against a fresh database without changing application records.

python verify.py --offline  # external-model boundary explicitly mocked
python verify.py           # real Gemini calls; requires configured credentials
"""

import argparse
import tempfile
from pathlib import Path
import pytest
from config import config as c


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    sandbox = None
    if not args.offline:
        sandbox = Path(tempfile.mkdtemp(prefix="clearauth-verification-"))
        c.APPLICATION_DATABASE_FILE = str(sandbox / "app.db")
        c.APPLICATION_DATABASE_URL = "sqlite:///" + c.APPLICATION_DATABASE_FILE
        c.CHECKPOINT_DATABASE_FILE = str(sandbox / "checkpoint.db")
        from run_database_setup import main as setup

        setup()
    flags = ["tests.py", "-q", "--tb=short"]
    if args.offline:
        flags += ["-p", "verification.offline_plugin"]
    print(
        "Verification mode:", "OFFLINE MODEL DOUBLE" if args.offline else "LIVE GEMINI"
    )
    print("Isolated records:", sandbox or "managed by the offline plugin")
    return pytest.main(flags)


if __name__ == "__main__":
    raise SystemExit(main())
