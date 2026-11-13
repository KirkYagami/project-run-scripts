#!/usr/bin/env bash
# ClearAuth AI container start: build whatever is missing, then serve API + dashboard.
# Artefacts live in volumes (database/, output/, processed/), so only the first start
# cleans the data, trains the models and builds the policy index.
set -euo pipefail
cd /app

if [ -z "${GEMINI_API_KEY:-}" ] || [ -z "${GEMINI_MODEL:-}" ]; then
    echo "GEMINI_API_KEY and GEMINI_MODEL must be set (put them in .env)." >&2
    exit 1
fi

# A step is done when all of its outputs exist.
step() {
    local label="$1" outputs="$2" out; shift 2
    for out in $outputs; do
        [ -e "$out" ] || { echo "==> $label"; python "$@"; return; }
    done
    echo "ok  $label (already built)"
}

echo "==> database tables and seed accounts (existing records kept)"
python run_database_setup.py
CLEAN="processed/authorisation_history_train_clean.csv processed/authorisation_history_eval_clean.csv processed/surgical_stays_train_clean.csv processed/surgical_stays_eval_clean.csv processed/clinical_note_sentences_clean.csv"
MODELS="output/models/approval_model.pkl output/models/stay_model.pkl output/models/evidence_model.pkl output/models/approval_features.json output/models/stay_features.json output/model_metrics.json"
step "clean the five raw extracts" "$CLEAN output/data_quality_report.json" run_data_pipeline.py
step "train the three models"      "$MODELS"                                run_model_training.py
step "policy knowledge index"      "database/chroma_store/chroma.sqlite3"   run_knowledge_indexing.py

if [ "${RUN_TESTS:-0}" = "1" ]; then
    echo "==> offline checks (Gemini mocked)"
    HF_HUB_OFFLINE=1 python verify.py --offline || echo "some checks failed; serving anyway"
    HF_HUB_OFFLINE=1 python local_workflow_smoke.py || echo "smoke test failed; serving anyway"
fi

export CLEARAUTH_API_HOST=0.0.0.0 CLEARAUTH_API_PORT=8081
python run_api_service.py &
API_PID=$!

for _ in $(seq 1 180); do
    if python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8081/openapi.json', timeout=2)" >/dev/null 2>&1; then
        echo "==> API is up; starting the dashboard"
        cat <<'EOF'
Accounts you can sign in with (demo only):
  maria  / 11111111   UM Nurse Reviewer (also james, leena)
  carlos / 22222222   Intake Coordinator
  ravi   / 33333333   Provider Services Representative
EOF
        exec python -m streamlit run run_dashboard.py \
            --server.port 8080 --server.address 0.0.0.0 \
            --server.headless true --browser.gatherUsageStats false
    fi
    if ! kill -0 "$API_PID" 2>/dev/null; then
        echo "The API stopped during start-up." >&2
        wait "$API_PID"; exit 1
    fi
    sleep 1
done
echo "The API did not answer within 180 seconds." >&2
kill "$API_PID" 2>/dev/null || true
exit 1
