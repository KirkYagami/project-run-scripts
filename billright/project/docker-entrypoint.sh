#!/usr/bin/env bash
set -euo pipefail

python run_database_setup.py
([ -f output/models/cause_model.pkl ] || (python run_data_pipeline.py && python run_model_training.py))
([ -d database/chroma_store ] || python run_knowledge_indexing.py)

python run_api_service.py &
api_process_id=$!

for _ in $(seq 1 90); do
    if python -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:8081/docs', timeout=2)" \
            >/dev/null 2>&1; then
        exec streamlit run run_dashboard.py --server.port=8080 --server.address=0.0.0.0
    fi
    if ! kill -0 "$api_process_id" 2>/dev/null; then
        echo "The API service stopped before it became ready." >&2
        wait "$api_process_id"
    fi
    sleep 1
done

echo "The API service did not become ready within 90 seconds." >&2
kill "$api_process_id" 2>/dev/null || true
exit 1
