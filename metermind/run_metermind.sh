#!/usr/bin/env bash
# One command for MeterMind: install the requirements into the local Python (no venv), build
# every artefact that is missing, run the tests, then serve the API (Swagger at
# http://HOST:PORT/docs). PYTHON=/path/to/python picks the interpreter (default python3).
#
#   bash run_metermind.sh                # build what is missing, test, serve
#   bash run_metermind.sh --rebuild      # rebuild every artefact even if it exists
#   bash run_metermind.sh --skip-tests   # do not run the test suite
#   bash run_metermind.sh --no-serve     # build (and test) only, do not start the API
#   HOST=0.0.0.0 PORT=9000 bash run_metermind.sh
#
# Steps whose input data is missing are skipped with a warning. Steps that need the language
# model run only when GEMINI_API_KEY is set (in the environment or in .env).
set -euo pipefail
SELF="$(cd "$(dirname "$0")" && pwd)/$(basename "$0")"
cd "$(dirname "$SELF")"

REBUILD=0; RUN_TESTS=1; SERVE=1
for argument in "$@"; do
  case "$argument" in
    --rebuild) REBUILD=1 ;;
    --skip-tests) RUN_TESTS=0 ;;
    --no-serve) SERVE=0 ;;
    -h|--help) awk 'NR > 1 && /^#/ { print; next } NR > 1 { exit }' "$SELF"; exit 0 ;;
    *) echo "unknown option: $argument" >&2; exit 2 ;;
  esac
done
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"

say()  { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
note() { printf '    %s\n' "$*"; }
warn() { printf '\033[1;33m    ! %s\033[0m\n' "$*"; }

if [ ! -d data ] || [ ! -d metermind ]; then
  echo "Run this from the MeterMind project folder (needs ./data and ./metermind)." >&2
  exit 1
fi

# ------------------------------------------------------------------ 1. Python (no venv)
REQUIREMENTS="argon2-cffi>=25.0.0
chromadb>=1.5.0
fastapi>=0.141.0
google-genai>=2.0.0
httpx>=0.28.0
joblib>=1.5.0
langchain-core>=1.5.0
langgraph>=1.2.0
langgraph-checkpoint-sqlite>=3.1.0
numpy>=2.4.0
pandas>=3.0.0
pydantic>=2.13.0
pyjwt>=2.13.0
pypdf>=6.0.0
pytest>=8.0.0
python-dotenv>=1.1.0
scikit-learn>=1.9.0
sentence-transformers>=5.0.0
sqlalchemy>=2.0.0
starlette>=0.46.0
uvicorn>=0.30.0"

# Uses the interpreter already on the machine and installs into it directly.
# Set PYTHON=/path/to/python to choose a different one.
say "Python environment (no venv)"
PY="${PYTHON:-python3}"
command -v "$PY" >/dev/null 2>&1 || { echo "No '$PY' found; install Python 3.11+ or set PYTHON=." >&2; exit 1; }
"$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' \
  || { echo "$("$PY" -V 2>&1) is too old; Python 3.11+ is needed (set PYTHON=)." >&2; exit 1; }
note "using $("$PY" -c 'import sys; print(sys.executable, sys.version.split()[0])')"

install_requirements() {
  local log; log="$(mktemp)"
  if "$PY" -m pip install -q "$@" > "$log" 2>&1; then rm -f "$log"; return 0; fi
  if grep -q "externally-managed-environment" "$log"; then
    note "this Python is externally managed; retrying with --break-system-packages"
    rm -f "$log"
    "$PY" -m pip install -q --break-system-packages "$@"
    return
  fi
  cat "$log" >&2; rm -f "$log"; return 1
}
note "installing requirements (quick when already installed)"
REQ_FILE="$(mktemp)"; printf '%s\n' "$REQUIREMENTS" > "$REQ_FILE"
install_requirements -r "$REQ_FILE" || { rm -f "$REQ_FILE"; echo "Installing requirements failed." >&2; exit 1; }
rm -f "$REQ_FILE"
mkdir -p artifacts database output/logs processed_data

HAS_KEY=0
if [ -n "${GEMINI_API_KEY:-}" ] || grep -Eq '^[[:space:]]*GEMINI_API_KEY[[:space:]]*=[[:space:]]*[^[:space:]#]' .env 2>/dev/null; then
  HAS_KEY=1
fi

# Check the port now rather than after the build and the tests, so a port that is taken
# fails at once and says who holds it.
port_in_use() {
  "$PY" - "$HOST" "$PORT" <<'PYEOF'
import socket, sys
probe = socket.socket()
probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try:
    probe.bind((sys.argv[1], int(sys.argv[2])))
except OSError:
    sys.exit(0)
finally:
    probe.close()
sys.exit(1)
PYEOF
}
if [ "$SERVE" -eq 1 ] && port_in_use; then
  echo "Port $PORT on $HOST is already in use, so the API cannot start there." >&2
  if command -v lsof >/dev/null 2>&1; then
    lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >&2 || true
  elif command -v ss >/dev/null 2>&1; then
    ss -ltnp "sport = :$PORT" >&2 || true
  fi
  echo "Stop that process (often an earlier run of this script: kill <PID>)," >&2
  echo "or choose another port, e.g.  PORT=$((PORT + 1)) bash $(basename "$SELF")" >&2
  exit 1
fi

# ------------------------------------------------------------------ 2. Build artefacts
BUILT=0; SKIPPED=0; FAILED=0

# An output written "path#table" counts as built only when that SQLite file holds the table;
# an empty or half-made database file is not a built one.
has_table() {
  "$PY" - "$1" "$2" <<'PYEOF'
import sqlite3, sys
try:
    connection = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro", uri=True)
    found = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (sys.argv[2],)
    ).fetchone()
except sqlite3.Error:
    found = None
sys.exit(0 if found else 1)
PYEOF
}

# A step is up to date when every output exists (with its table, if one is named) and no
# input is newer than it - the same rule make uses, so rebuilding an input rebuilds what
# depends on it.
up_to_date() {
  local outputs="$1" inputs="$2" output path input
  for output in $outputs; do
    path="${output%%#*}"
    [ -e "$path" ] || return 1
    if [ "$output" != "$path" ]; then has_table "$path" "${output#*#}" || return 1; fi
    for input in $inputs; do
      if [ "$input" -nt "$path" ]; then return 1; fi
    done
  done
  return 0
}

# step "name" "inputs (space separated)" "outputs (space separated)" optional(0|1) command...
step() {
  local name="$1" inputs="$2" outputs="$3" optional="$4"; shift 4
  local missing="" path
  for path in $inputs; do [ -e "$path" ] || missing="$missing $path"; done
  if [ -n "$missing" ]; then
    warn "skip  $name (missing input:$missing)"; SKIPPED=$((SKIPPED + 1)); return 0
  fi
  if [ "$REBUILD" -eq 0 ] && up_to_date "$outputs" "$inputs"; then
    note "ok    $name (up to date)"; return 0
  fi
  note "build $name"
  if "$@"; then
    BUILT=$((BUILT + 1))
  elif [ "$optional" -eq 1 ]; then
    warn "$name failed; carrying on because it is optional"; FAILED=$((FAILED + 1))
  else
    echo "Build step '$name' failed." >&2; exit 1
  fi
}

py()  { "$PY" -c "$1"; }
mod() { "$PY" -m "$1"; }

say "Building artefacts (pass --rebuild to redo all)"

TRAIN=data/reading_book_train.csv
PREDICT=data/reading_book_predict.csv
CLEAN=processed_data/readings_clean.csv
READINGS_DB=database/metermind.sqlite
CHAMPION=artifacts/champion_exception.joblib
RULE=output/operating_rule.json
COMPLAINTS=data/complaint_messages.csv
URGENCY_MODEL=artifacts/complaint_urgency.joblib
CHUNKS=processed_data/tariff_chunks.json
STORE=database/tariff_store

# Readings: clean, load, report, model, queue.
step "clean the reading book"  "$TRAIN" "$CLEAN processed_data/readings_rejected.csv" 0 \
  py "from config import constants as c
from metermind.data_access.cleaning_pipeline import clean_reading_book
print('   ', clean_reading_book(c.READING_BOOK_TRAIN_PATH, c.CLEAN_READING_BOOK_PATH, c.REJECTED_READING_BOOK_PATH))"
step "load the readings database" "$CLEAN" "$READINGS_DB#readings" 0 mod metermind.data_access.database_loader
step "reading reports"         "$READINGS_DB" "output/reading_reports.csv" 0 mod metermind.data_access.database_reports
step "baseline model"          "$CLEAN" "artifacts/baseline_exception.joblib output/baseline_scores.json" 0 \
  mod metermind.exception_models.baseline_model
step "tree models"             "$CLEAN" "artifacts/tree_exception.joblib artifacts/forest_exception.joblib" 0 \
  mod metermind.exception_models.tree_models
step "cross validation"        "$CLEAN" "output/cross_validation.csv" 0 mod metermind.exception_models.cross_validation
step "feature engineering"     "$CLEAN" "processed_data/readings_widened.csv output/feature_lift.json" 0 \
  mod metermind.exception_models.feature_engineering
step "champion and operating rule" "$CLEAN" "$CHAMPION $RULE" 0 mod metermind.exception_models.champion_model
step "exception report"        "$CLEAN $CHAMPION" "output/exception_report.csv" 0 \
  mod metermind.exception_models.exception_report
step "investigation queues"    "$PREDICT $CHAMPION $RULE" "output/queue_vigilance.csv output/queue_billing.csv" 0 \
  mod metermind.exception_models.investigation_queues

# Complaints: classify, clean, summarise, extract.
step "complaint classifiers"   "$COMPLAINTS" "artifacts/complaint_category.joblib $URGENCY_MODEL output/complaint_scores.json" 0 \
  mod metermind.message_intelligence.complaint_classifier
step "clean complaints"        "$COMPLAINTS" "processed_data/complaints_clean.csv" 0 mod metermind.message_intelligence.text_cleaning
step "thread summaries"        "data/message_threads.csv" "output/thread_summaries.csv" 0 \
  mod metermind.message_intelligence.thread_summary
step "reference extraction"    "$COMPLAINTS data/connection_register.csv" "output/extracted_references.csv" 0 \
  mod metermind.message_intelligence.reference_extraction

# Tariff orders: chunk and embed (the embedding model downloads on first use).
step "tariff chunks"           "data/tariff_orders_manifest.json data/tariff_orders" "$CHUNKS" 0 mod metermind.retrieval.chunking
step "tariff vector store"     "$CHUNKS" "$STORE" 0 mod metermind.retrieval.vector_store

# Language-model steps: only with a key, and never fatal.
if [ "$HAS_KEY" -eq 1 ]; then
  step "escalations (LLM)"       "$COMPLAINTS $URGENCY_MODEL" "output/escalations.csv" 1 mod metermind.message_intelligence.escalation
  step "grounded answers (LLM)"  "$STORE data/retrieval_evaluation_set.json" "output/tariff_answers.csv" 1 mod metermind.retrieval.grounded_answer
  step "filtered answers (LLM)"  "$STORE data/retrieval_evaluation_set.json data/tariff_orders_manifest.json" "output/filtered_answers.csv" 1 \
    mod metermind.retrieval.filtered_search
else
  warn "skip  LLM steps (escalations, grounded and filtered answers): GEMINI_API_KEY is not set"
  SKIPPED=$((SKIPPED + 3))
fi
note "built $BUILT, skipped $SKIPPED, optional failures $FAILED"

# ------------------------------------------------------------------ 3. Tests
if [ "$RUN_TESTS" -eq 1 ]; then
  say "Running the test suite"
  # The root suite and pytest/tests.py share in-memory state (e.g. signed-up accounts), so
  # each runs in its own process.
  TESTS_OK=1
  ROOT_TESTS=$(ls test_*.py 2>/dev/null || true)
  if [ -n "$ROOT_TESTS" ]; then
    note "suite 1: $(echo $ROOT_TESTS | wc -w | tr -d ' ') root test files"
    # shellcheck disable=SC2086
    "$PY" -m pytest -q -p no:cacheprovider $ROOT_TESTS || TESTS_OK=0
  fi
  if [ -f pytest/tests.py ]; then
    note "suite 2: pytest/tests.py"
    "$PY" -m pytest -q -p no:cacheprovider pytest/tests.py || TESTS_OK=0
  fi
  if [ "$TESTS_OK" -eq 1 ]; then
    note "all tests passed"
  else
    warn "some tests failed (see above)"
  fi
fi

# ------------------------------------------------------------------ 4. Serve
if [ "$SERVE" -eq 1 ]; then
  say "Starting MeterMind on http://$HOST:$PORT  (Swagger: http://$HOST:$PORT/docs, Ctrl+C to stop)"
  [ -e "$CHAMPION" ] || warn "no champion model: /api/v1/screening will answer 503"
  [ -e "$URGENCY_MODEL" ] || warn "no complaint classifiers: /api/v1/assistant/questions cannot triage"
  [ "$HAS_KEY" -eq 1 ] || warn "no GEMINI_API_KEY: the assistant endpoints will answer 503"
  # Behind a path proxy (VS Code / code-server labs serve the app at /proxy/<port>/), the app
  # must know that prefix or Swagger asks for /openapi.json outside the proxy and stays blank.
  # ROOT_PATH wins when set (even empty); otherwise it is read from VSCODE_PROXY_URI.
  if [ -z "${ROOT_PATH+set}" ] && [ -n "${VSCODE_PROXY_URI:-}" ]; then
    PROXIED="${VSCODE_PROXY_URI//\{\{port\}\}/$PORT}"
    case "$PROXIED" in
      *://*/*) ROOT_PATH="/${PROXIED#*://*/}" ;;
      *) ROOT_PATH="${PROXIED#.}"; ROOT_PATH="/${ROOT_PATH#/}" ;;
    esac
  fi
  ROOT_PATH="${ROOT_PATH:-}"; ROOT_PATH="${ROOT_PATH%/}"
  if [ -n "$ROOT_PATH" ]; then
    note "serving under the proxy prefix $ROOT_PATH (open <your lab URL>$ROOT_PATH/docs)"
  fi
  exec "$PY" -c "
import uvicorn
from config import constants
from metermind.api.application_factory import build_application
uvicorn.run(build_application(constants.ORM_DATABASE_PATH), host='$HOST', port=$PORT,
            root_path='$ROOT_PATH', proxy_headers=True, forwarded_allow_ips='*')"
fi
