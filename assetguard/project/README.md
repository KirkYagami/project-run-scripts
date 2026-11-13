# AssetGuard AI: Docker build

A clean, runnable copy of `p1/Project` packaged as a single container that serves:

| Port | Service |
|------|---------|
| 8080 | Streamlit dashboard |
| 8081 | REST API (Swagger UI at `/docs`) |

The image contains the trained models (`output/models`), the manual knowledge index
(`database/chroma_store`), the manuals (`data/docs`), the live fleet
(`data/input/current_fleet.csv`), the cleaned technician notes, and the
`all-MiniLM-L6-v2` embedding model, so it needs no downloads at start-up.
The only outside service it calls is Gemini.

## Run

```bash
cp .env.example .env          # then put your real GEMINI_API_KEY in .env
docker compose up --build -d
docker compose logs -f        # wait for "Uvicorn running" and the Streamlit URL
```

Open http://localhost:8080 and sign in with one of the seeded accounts that
`run_database_setup.py` prints in the logs (they come from `SEED_USER_ACCOUNTS` in
`config/config.py`; demo use only).

Without compose:

```bash
docker build -t assetguard-ai .
docker run -d --name assetguard-ai --env-file .env \
  -p 8080:8080 -p 8081:8081 -v assetguard-state:/app/state assetguard-ai
```

## Data that persists

`assetguard.db` (users, work orders, reviews, chat history, LLM call log) and
`checkpoint.db` (paused LangGraph runs waiting for a supervisor) live in `/app/state`,
which is the `assetguard-state` volume. Each one is created on first start.
`docker compose down -v` wipes it back to a fresh install.

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `GEMINI_API_KEY` | (required) | Language model key; the container refuses to start without it |
| `GEMINI_MODEL` | `gemini-3.1-flash-lite` | Model name |
| `STATE_DIRECTORY` | `/app/state` in the image | Folder for the two SQLite files |
| `API_PORT` | `8081` | REST service port |
| `API_BASE_URL` | `http://localhost:8081` | Where the dashboard finds the API |

## How this differs from `p1/Project`

- Code is unchanged apart from `config/config.py`: `API_PORT`, `API_BASE_URL` and the
  SQLite folder (`STATE_DIRECTORY`) can now be set from the environment. The defaults
  are the original values, so a local run behaves the same.
- `.streamlit/config.toml` uses `headless = true`.
- `requirements.txt` is pinned to the versions the models were trained with.
- Not included: `.env`, the local databases, the raw and processed training CSVs (except
  `technician_notes_clean.csv`, which the API reads), `tests.py`, caches.
  To retrain, copy the raw CSVs into `data/` and run `run_data_preparation.py` and
  `run_model_training.py` in a full checkout.
