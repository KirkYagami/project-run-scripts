# BreachWatch AI on EC2

Two scripts that deploy BreachWatch AI (incident triage and breach reporting: Streamlit
dashboard, REST API, a five-agent LangGraph assessment that waits for the DPO, ML models
and a procedure index, with Gemini) to a fresh EC2 instance with Docker Compose.

| Script | What it does |
| --- | --- |
| `build_project.sh` | Writes the whole project (code, Dockerfile, compose.yml, raw data, procedure PDFs) into a folder and checks every file's SHA-256. |
| `run_on_ec2.sh` | Installs Docker and the Compose plugin, adds swap on small machines, runs `build_project.sh`, writes `.env`, builds the image and starts it with `docker compose up -d`. |

Same setup as the ClearAuth and BillRight scripts, which were tested end to end on Ubuntu
24.04 (and the Docker + Compose install on Amazon Linux 2023). The BreachWatch end-to-end
test is still in progress.

The [`project/`](project/) folder holds every file `build_project.sh` writes (code, Dockerfile,
compose file, entrypoint, data), so you can browse the code on GitHub. To deploy you still
only need the two scripts; regenerate `project/` with `bash build_project.sh project` after
updating the script.

## 1. Launch the instance

- **Type:** t3.large (2 vCPU, 8 GB) or bigger. Smaller machines get a 4 GB swap file but train slowly.
- **Disk:** 25 GB or more. The build needs about 10 GB free.
- **Security group:** allow inbound TCP **8080** (dashboard), and **8081** if you want the API and Swagger.

## 2. Copy the scripts and run

```bash
# from your machine (use ubuntu@ on Ubuntu, ec2-user@ on Amazon Linux)
scp -i key.pem build_project.sh run_on_ec2.sh ec2-user@<public-ip>:~

# on the instance
GEMINI_API_KEY=your-key bash run_on_ec2.sh
```

Or clone this repo on the instance and run `bash breachwatch/run_on_ec2.sh`.
If `GEMINI_API_KEY` is not set, the script asks for it (input is hidden).

The image build takes 5 to 10 minutes (Python packages and the embedding model). The
**first start** then cleans the data, trains the three models and builds the procedure
index, which takes a few more minutes. The script waits for all of it and then prints:

```
Dashboard : http://<public-ip>:8080
REST API  : http://<public-ip>:8081/docs
```

Later starts are quick: the models and index are kept in Docker volumes.

## 3. Sign in

| User | Password | Role |
| --- | --- | --- |
| `ines` (also `arjun`, `katarzyna`) | `11111111` | Data Protection Officer |
| `priya` (also `tomasz`, `kadri`, `joao`, `meera`, `rasmus`) | `22222222` | Security Analyst |
| `ananya` (also `mateusz`, `liis`, `beatriz`, `rohan`, `marta`) | `33333333` | Customer Communications Agent |

These are seeded demo accounts.

## Day-to-day

Run these from the project folder, `~/breachwatch-ai`:

| Task | Command |
| --- | --- |
| Stop | `docker compose down` |
| Start | `docker compose up -d` |
| Follow logs | `docker compose logs -f` |
| Status | `docker compose ps` |
| Rebuild after a code change | `docker compose up -d --build` |
| Reset all data (retrains on next start) | `docker compose down -v` |
| Run `tests.py` on start | add `RUN_TESTS=1` to `.env`, then `docker compose up -d` |
| Recreate the code from scratch | `rm -rf ~/breachwatch-ai && bash run_on_ec2.sh` |

Use `sudo docker ...` until you log in again (the script adds you to the `docker` group).

## Options

Set these as environment variables before `run_on_ec2.sh`. They are saved in `.env`,
which `docker compose` reads, so later `up`/`down` use the same values.

| Variable | Default | Purpose |
| --- | --- | --- |
| `GEMINI_API_KEY` | asked for | Gemini key (`.env` is mode 600) |
| `GEMINI_MODEL` | `gemini-3.1-flash-lite` | Model name |
| `APP_DIR` | `~/breachwatch-ai` | Where the project is written |
| `DASHBOARD_PORT` | `8080` | Host port for the dashboard |
| `API_PORT` | `8081` | Host port for the REST API |
| `API_BIND` | `0.0.0.0` | Set `127.0.0.1` to keep the API private; then reach Swagger with `ssh -L 8081:127.0.0.1:8081 ec2-user@<ip>` and open http://localhost:8081/docs |

## Data that persists

| Volume | Holds |
| --- | --- |
| `breachwatch_breachwatch_database` | `breachwatch.db` (users, assessments, DPO decisions, chat history, LLM call log), `checkpoint.db` (assessments paused for the DPO), the procedure index |
| `breachwatch_breachwatch_output` | trained models and metrics |
| `breachwatch_breachwatch_processed` | cleaned training data |

## Troubleshooting

- **Page doesn't load:** check that the security group allows the port, and use `http://`, not `https://`.
- **"Only N GB free disk":** grow the EBS volume, then run the script again.
- **Container stopped:** the script prints the last 40 log lines. Check `docker compose logs`.
- **Assessments or chat fail:** the Gemini key or model name in `~/breachwatch-ai/.env` is wrong. Fix it, then `docker compose up -d`.
- **Amazon Linux prints "legacy builder is deprecated":** harmless.
