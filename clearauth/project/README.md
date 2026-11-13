# ClearAuth AI

Prior-authorisation screening and human-reviewed decision support for Brightwater Health Plan, implemented to the supplied p7 contracts.

## Setup and run (one command, no venv)

From `workspace/Project` (the folder holding `data/`):

```sh
bash build_clearauth.sh
```

This writes the source, installs `requirements-lock.txt` (`requirements-py311.txt` on Python 3.11) straight into the current `python3` (no virtual environment; `PYTHON=/path/to/python` picks another), builds only the artefacts that are missing or stale, runs the offline checks, then starts the API and the dashboard together. Ctrl+C stops both.

| Option | Effect |
| --- | --- |
| `--skip-tests` | do not run the offline checks |
| `--rebuild` | reinstall packages and rebuild every artefact |
| `--api-only` | serve only the API + Swagger |
| `--no-serve` | build (and test) only |
| `--no-install` | use the packages already installed |
| `--write-only` | only write the source files |

Ports: `API_PORT` (default 8081), `DASHBOARD_PORT` (default 8080), `HOST` (default 0.0.0.0). Behind a VS Code / code-server path proxy, the Swagger prefix is taken from `VSCODE_PROXY_URI`, or set `ROOT_PATH=/proxy/8081`.

Configure `GEMINI_API_KEY` and `GEMINI_MODEL` in `.env`. Never commit `.env`. All language-model calls use the Google GenAI SDK, with automatic tool calling and SDK retries disabled. No live clinical determination is made by a model.

## Swagger

Open `http://localhost:8081/docs`. Call `POST /auth/signin` with e.g. `{"username": "maria", "password": "11111111"}` and paste the returned `session_token` into the `X-Session-Token` field of each guarded call. The build script also prints a ready-made token at start-up. Signing the same user in again replaces their token, so use different users in Swagger and the dashboard.

## Individual steps

```sh
python3 run_database_setup.py
python3 run_data_pipeline.py
python3 run_model_training.py
python3 run_knowledge_indexing.py
python3 run_api_service.py
python3 -m streamlit run run_dashboard.py   # second terminal
```

The dashboard is at `http://localhost:8080`; REST documentation is at `http://localhost:8081/docs`. Knowledge indexing downloads `all-MiniLM-L6-v2` on first use, unless it is already cached. Keep the embedding cache available when running offline. The service checks that build artifacts exist before importing runtime components.

Database setup is idempotent and seeds the 14 accounts specified in `config/config.py`. The provided training/demo passwords are defined there. Examples are `carlos` (Intake Coordinator), `maria` and `leena` (UM Nurse Reviewers), and `ravi` (Provider Services Representative). Use a different nurse from the person who opened a review to decide it. These accounts and seed passwords are for the supplied local project; real deployment requires an appropriate identity and account-management process.

## Workflow

1. Sign in and choose a request from the urgent-first review queue.
2. Inspect the questionnaire screening, policy sentences, evidence findings, disagreements and internal predictions.
3. Open a review with a question for the review team. Exactly five model calls establish the recommendation.
4. The workflow persists a checkpoint and waits for an independent nurse.
5. That nurse records one of the decisions the screening permits. Approval generates a provider letter and a member notice (seven calls total); an information request generates its provider letter (six); referral stores a summary (five).
6. Inspect the final record, correspondence, decision reason and call budget in Audit trail.

The chart on Request detail is drawn directly as SVG. No `.dot` files or Graphviz dependency are used.

## Validation

The unmodified supplied suite is:

```sh
python -m pytest tests.py -q
```

This command includes real Gemini calls and requires valid credentials and network access. It creates reviews in the configured application database. Use a fresh, isolated database/checkpoint pair for repeatable live test runs; do not delete a database containing records you need.

For deterministic offline contract checks:

```sh
HF_HUB_OFFLINE=1 python -m pytest tests.py -p verification.offline_plugin -q
```

The explicit plugin uses a temporary application database and replaces only the external language-model boundary. It uses the actual supplied data, fitted models, tools, vector index, API, database code and LangGraph workflow. It is not imported by the application or by the normal test command. Its pass result verifies contracts and workflow behaviour, not Gemini output quality.

Additional offline branch checks:

```sh
HF_HUB_OFFLINE=1 python local_workflow_smoke.py
```

All three decision paths, durable pause/reopen and duplicate-decision rejection are checked without making external model calls.

## Data and model results

The cleaning pipeline retains 29,842 authorisation training rows, 7,467 authorisation evaluation rows, 29,782 stay training rows, 7,436 stay evaluation rows, and 35,695 evidence sentences. The knowledge build reads 16 PDFs and 145 sections, producing 205 sentence-aware passages with this implementation.

Validated held-out model scores: approval ROC-AUC **0.9232**, stay R-squared **0.7057**, evidence macro-F1 **0.9399**. Full scores, algorithm names, training/evaluation row counts and library version are in `output/model_metrics.json`. Training saves artifacts only after all three minimums pass. Imputation, encoding and word vectorisation are saved within each fitted pipeline.

## Boundaries

- Policy criteria and their figures are parsed from the appropriate service PDF, never copied into code. Exact Decimal arithmetic controls BMI and policy boundaries.
- Documents never fill or overwrite questionnaire answers. Their sentence evidence is linked to the request's own criteria.
- Every dashboard result comes through the REST service. Server-side access rules are enforced independently of page visibility.
- Member numbers are withheld from chat prompts and chat records; request-status replies come from deterministic, role-aware record access. Provider representatives cannot receive internal predictions.
- The casebook remains indexed for the supplied corpus but is excluded from every chat search.
- Final decisions, status changes and correspondence are stored together in one transaction. Checkpoints are persistent SQLite; application records are separate SQLAlchemy/SQLite tables. Per-request locks prevent concurrent work inside this single service process, and unique constraints enforce one review/decision.
- This is the specified local reference deployment. Multiple API workers require a cross-process locking/job design and operational infrastructure; do not claim the current in-process locks provide distributed coordination.
- Generated letters and notices are stored for review. No email or external message is sent by this application.
