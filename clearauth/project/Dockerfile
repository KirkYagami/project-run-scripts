# ClearAuth AI: one image serving the dashboard (8080) and the REST API (8081).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app

# CPU-only torch first, so the locked versions below never pull the CUDA build.
COPY requirements-lock.txt requirements.txt ./
RUN pip install "torch==$(grep -E '^torch==' requirements-lock.txt | cut -d= -f3)" \
        --index-url https://download.pytorch.org/whl/cpu \
 && pip install -r requirements-lock.txt

# Bake the embedding model into the image so the first start needs no download.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY . .
RUN chmod +x docker-entrypoint.sh

EXPOSE 8080 8081
CMD ["bash", "/app/docker-entrypoint.sh"]
