FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/opt/hf \
    STATE_DIRECTORY=/app/state \
    ANONYMIZED_TELEMETRY=False

WORKDIR /app

RUN useradd --create-home --uid 1000 app && mkdir -p /app/state /opt/hf && chown app:app /app /app/state /opt/hf

COPY requirements.txt .
RUN pip install -r requirements.txt

# Bake the embedding model into the image so the container starts offline.
USER app
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
ENV HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1

COPY --chown=app:app --chmod=755 entrypoint.sh .
COPY --chown=app:app . .

# A source-only checkout (e.g. made by deploy/build_project.sh) ships the raw CSVs
# but no trained models or vector index: build them here. Seeded, so the models
# match output/model_metrics.json. Skipped when the artifacts are already present.
RUN if [ ! -f output/models/breakdown_model.pkl ] || [ ! -d database/chroma_store ]; then \
        python run_data_preparation.py \
        && python run_model_training.py \
        && python run_knowledge_indexing.py \
        && rm -f data/*.csv; \
    fi

VOLUME ["/app/state"]
EXPOSE 8080 8081

HEALTHCHECK --interval=30s --timeout=5s --start-period=90s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8081/docs', timeout=4)" || exit 1

ENTRYPOINT ["./entrypoint.sh"]
