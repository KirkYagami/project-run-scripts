#!/usr/bin/env bash
# One command for LoanServe: set up Python, build every artefact that is missing, run the
# tests, then serve the API (Swagger at http://HOST:PORT/docs).
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
cd "$(dirname "$0")"

REBUILD=0; RUN_TESTS=1; SERVE=1
for argument in "$@"; do
  case "$argument" in
    --rebuild) REBUILD=1 ;;
    --skip-tests) RUN_TESTS=0 ;;
    --no-serve) SERVE=0 ;;
    -h|--help) sed -n '2,13p' "$0"; exit 0 ;;
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

# ------------------------------------------------------------------ 1. Python environment
say "Python environment"
if [ ! -x .venv/bin/python ]; then
  if command -v uv >/dev/null 2>&1; then
    note "creating .venv with uv (Python 3.12)"
    uv venv .venv --python 3.12 -q
  else
    PYTHON=""
    for candidate in python3.12 python3.13 python3.11 python3; do
      if command -v "$candidate" >/dev/null 2>&1; then PYTHON="$candidate"; break; fi
    done
    [ -n "$PYTHON" ] || { echo "No python3 found; install Python 3.11+ first." >&2; exit 1; }
    note "creating .venv with $PYTHON"
    "$PYTHON" -m venv .venv
  fi
fi
PY=.venv/bin/python
"$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' \
  || { echo ".venv uses Python older than 3.11; delete .venv and re-run." >&2; exit 1; }

STAMP=.venv/.loanserve-requirements
if [ ! -f "$STAMP" ] || ! cmp -s requirements.txt "$STAMP"; then
  note "installing requirements.txt (first run, or it changed)"
  if command -v uv >/dev/null 2>&1; then
    uv pip install -q --python "$PY" -r requirements.txt
  else
    "$PY" -m pip install -q --upgrade pip
    "$PY" -m pip install -q -r requirements.txt
  fi
  cp requirements.txt "$STAMP"
else
  note "requirements already installed"
fi
mkdir -p artifacts database output/logs processed_data

# The project (and its tests) expect a .env declaring the model settings. An existing one is
# never touched; a missing one gets a template with empty values for you to fill in.
if [ ! -f .env ]; then
  printf '%s\n' "# Fill these in to use the language model; never commit real values." \
    "GEMINI_API_KEY=" "GEMINI_MODEL=" > .env
  note "created a .env template (GEMINI_API_KEY / GEMINI_MODEL are empty)"
fi

# ------------------------------------------------------------------ 2. Build artefacts
BUILT=0; SKIPPED=0

# step "name" "inputs (space separated)" "outputs (space separated)" command...
step() {
  local name="$1" inputs="$2" outputs="$3"; shift 3
  local missing="" path
  for path in $inputs; do [ -e "$path" ] || missing="$missing $path"; done
  if [ -n "$missing" ]; then
    warn "skip  $name (missing input:$missing)"; SKIPPED=$((SKIPPED + 1)); return 0
  fi
  if [ "$REBUILD" -eq 0 ]; then
    local all_there=1
    for path in $outputs; do [ -e "$path" ] || all_there=0; done
    if [ "$all_there" -eq 1 ]; then note "ok    $name (already built)"; return 0; fi
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
step "load the application database" "$CLEANED" "$DB" mod loanserve.data_access.database_loader
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
  if .venv/bin/pytest -q -p no:cacheprovider test.py; then
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
  exec "$PY" -c "
import os, uvicorn
from loanserve.api.application_factory import create_application
uvicorn.run(create_application(database_url=os.environ.get('LOANSERVE_DATABASE_URL') or None),
            host='$HOST', port=$PORT)"
fi
