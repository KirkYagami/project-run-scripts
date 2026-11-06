#!/usr/bin/env bash
# One command for LoanServe: install the requirements into the local Python (no venv), build
# every artefact that is missing, run the tests, then serve the API (Swagger at
# http://HOST:PORT/docs). PYTHON=/path/to/python picks the interpreter (default python3).
#
#   bash run_loanserve.sh                # build what is missing, test, serve
#   bash run_loanserve.sh --rebuild      # rebuild every artefact even if it exists
#   bash run_loanserve.sh --skip-tests   # do not run the test suite
#   bash run_loanserve.sh --no-serve     # build (and test) only, do not start the API
#   HOST=0.0.0.0 PORT=9000 bash run_loanserve.sh
#   LOANSERVE_DATABASE_URL=sqlite:///database/api.db bash run_loanserve.sh   # keep API data
#
# Steps whose input data is missing are skipped with a warning.
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

if [ ! -d data ] || [ ! -d loanserve ] || [ ! -f requirements.txt ]; then
  echo "Run this from the LoanServe Project folder (needs ./data, ./loanserve, requirements.txt)." >&2
  exit 1
fi

# ------------------------------------------------------------------ 1. Python (no venv)
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
note "installing requirements.txt (quick when already installed)"
install_requirements -r requirements.txt || { echo "Installing requirements failed." >&2; exit 1; }
mkdir -p artifacts database output/logs processed_data

# The project (and its tests) expect a .env declaring the model settings. An existing one is
# never touched; a missing one gets a template with empty values for you to fill in.
if [ ! -f .env ]; then
  printf '%s\n' "# Fill these in to use the language model; never commit real values." \
    "GEMINI_API_KEY=" "GEMINI_MODEL=" > .env
  note "created a .env template (GEMINI_API_KEY / GEMINI_MODEL are empty)"
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
BUILT=0; SKIPPED=0

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

# step "name" "inputs (space separated)" "outputs (space separated)" command...
step() {
  local name="$1" inputs="$2" outputs="$3"; shift 3
  local missing="" path
  for path in $inputs; do [ -e "$path" ] || missing="$missing $path"; done
  if [ -n "$missing" ]; then
    warn "skip  $name (missing input:$missing)"; SKIPPED=$((SKIPPED + 1)); return 0
  fi
  if [ "$REBUILD" -eq 0 ] && up_to_date "$outputs" "$inputs"; then
    note "ok    $name (up to date)"; return 0
  fi
  note "build $name"
  "$@" || { echo "Build step '$name' failed." >&2; exit 1; }
  BUILT=$((BUILT + 1))
}
mod() { "$PY" -m "$1" > /dev/null; }

say "Building artefacts (pass --rebuild to redo all)"

TRAIN=data/loan_applications_train.csv
PREDICT=data/loan_applications_predict.csv
CLEANED=processed_data/loan_applications_cleaned.csv
PREDICT_CLEANED=processed_data/loan_applications_predict_cleaned.csv
PREDICT_ENRICHED=processed_data/loan_applications_predict_enriched.csv
DB=database/loanserve.db
CHAMPION=artifacts/champion.pkl
THRESHOLD=output/threshold_choice.json
MESSAGES=data/customer_messages.csv
THREADS=data/message_threads.csv
CLASSIFIER=artifacts/message_classifier.pkl

# Applications: clean, load, enrich, model, queue.
step "clean the application books" "$TRAIN $PREDICT" "$CLEANED $PREDICT_CLEANED output/rejected_records.csv" \
  mod loanserve.data_access.cleaning_pipeline
step "load the application database" "$CLEANED" "$DB#loan_applications" mod loanserve.data_access.database_loader
step "feature engineering"   "$CLEANED $PREDICT_CLEANED" \
  "processed_data/loan_applications_enriched.csv $PREDICT_ENRICHED output/feature_lift.json" \
  mod loanserve.risk_models.feature_engineering
step "baseline model"        "$CLEANED $PREDICT_CLEANED" "artifacts/baseline_model.pkl output/predictions.csv" \
  mod loanserve.risk_models.baseline_model
step "tree models"           "$CLEANED" "artifacts/decision_tree.pkl artifacts/random_forest.pkl output/class_weight_comparison.json" \
  mod loanserve.risk_models.tree_models
step "cross validation"      "$CLEANED" "output/fold_scores.json" mod loanserve.risk_models.cross_validation
step "champion and threshold" "$CLEANED" "$CHAMPION output/champion_search.json $THRESHOLD" \
  mod loanserve.risk_models.champion_model
step "work queue"            "$CHAMPION $PREDICT_ENRICHED $THRESHOLD" "output/work_queue.csv" \
  mod loanserve.risk_models.work_queue

# Messages: clean, classify, summarise, extract, guard, batch, escalate.
step "clean messages"        "$MESSAGES" "processed_data/messages_cleaned.csv" mod loanserve.message_intelligence.text_cleaning
step "message classifier"    "$MESSAGES" "$CLASSIFIER" mod loanserve.message_intelligence.message_classifier
step "thread summaries"      "$THREADS" "output/thread_summaries.csv" mod loanserve.message_intelligence.thread_summary
step "entity extraction"     "$MESSAGES $DB" "output/message_entities.csv" mod loanserve.message_intelligence.entity_extraction
step "injection report"      "data/adversarial_messages.csv $CLASSIFIER" "output/injection_report.csv" \
  mod loanserve.message_intelligence.injection_guard
step "message batch pipeline" "$MESSAGES $CLASSIFIER $DB" "output/message_pipeline.csv" \
  mod loanserve.message_intelligence.batch_pipeline
step "escalation report"     "$THREADS $CLASSIFIER $DB" "output/escalation_report.csv" \
  mod loanserve.message_intelligence.escalation

# Policy documents: chunk and embed (the embedding model downloads on first use).
step "policy vector store"   "data/policy_documents data/policy_documents_manifest.json" "database/policy_store/chroma.sqlite3" \
  mod loanserve.retrieval.vector_store
note "built $BUILT, skipped $SKIPPED"

# ------------------------------------------------------------------ 3. Tests
if [ "$RUN_TESTS" -eq 1 ]; then
  say "Running the test suite"
  if "$PY" -m pytest -q -p no:cacheprovider test.py; then
    note "all tests passed"
  else
    warn "some tests failed (see above)"
  fi
fi

# ------------------------------------------------------------------ 4. Serve
if [ "$SERVE" -eq 1 ]; then
  say "Starting LoanServe on http://$HOST:$PORT  (Swagger: http://$HOST:$PORT/docs, Ctrl+C to stop)"
  note "sign up at POST /api/v1/auth/signup (role: administrator or loan_officer), log in, then Authorize"
  [ -n "${LOANSERVE_DATABASE_URL:-}" ] || note "applications and accounts are kept in memory; set LOANSERVE_DATABASE_URL to keep applications"
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
import os, uvicorn
from loanserve.api.application_factory import create_application
uvicorn.run(create_application(database_url=os.environ.get('LOANSERVE_DATABASE_URL') or None),
            host='$HOST', port=$PORT, root_path='$ROOT_PATH',
            proxy_headers=True, forwarded_allow_ips='*')"
fi
