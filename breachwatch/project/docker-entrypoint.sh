#!/usr/bin/env bash
# BreachWatch AI container start: build whatever is missing, then serve API + dashboard.
# Artefacts live in volumes (database/, output/, processed/), so only the first start
# cleans the data, trains the models and builds the procedure index.
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
CLEAN="processed/security_incidents_train_clean.csv processed/security_incidents_eval_clean.csv processed/containment_effort_train_clean.csv processed/containment_effort_eval_clean.csv processed/analyst_incident_notes_clean.csv"
MODELS="output/models/harm_model.pkl output/models/effort_model.pkl output/models/attack_model.pkl output/models/harm_features.json output/models/effort_features.json output/model_metrics.json"
step "clean the five raw extracts" "$CLEAN output/data_quality_report.json" run_data_pipeline.py
step "train the three models"      "$MODELS"                                run_model_training.py
step "procedure knowledge index"   "database/chroma_store/chroma.sqlite3"   run_knowledge_indexing.py

if [ "${RUN_TESTS:-0}" = "1" ]; then
    echo "==> python -m pytest tests.py"
    HF_HUB_OFFLINE=1 python -m pytest tests.py -q || echo "some tests failed; serving anyway"
fi

python run_api_service.py &
API_PID=$!

for _ in $(seq 1 180); do
    if python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8081/openapi.json', timeout=2)" >/dev/null 2>&1; then
        echo "==> API is up; starting the dashboard"
        cat <<'EOF'
Accounts you can sign in with (demo only):
  ines    / 11111111   Data Protection Officer (also arjun, katarzyna)
  priya   / 22222222   Security Analyst
  ananya  / 33333333   Customer Communications Agent
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
