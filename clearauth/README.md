# ClearAuth AI on EC2

Two scripts that deploy ClearAuth AI (prior authorisation review: Streamlit dashboard,
REST API, LangGraph agents, ML models and a medical-policy index, with Gemini) to a
fresh EC2 instance with Docker Compose.

| Script | What it does |
| --- | --- |
| `build_project.sh` | Writes the whole project (code, Dockerfile, compose.yml, raw data, policy PDFs) into a folder and checks every file's SHA-256. |
| `run_on_ec2.sh` | Installs Docker and the Compose plugin, adds swap on small machines, runs `build_project.sh`, writes `.env`, builds the image and starts it with `docker compose up -d`. |

Tested on Ubuntu 24.04: full run, the project's offline checks (50 tests and the workflow
smoke test) inside the container, and `docker compose down` / `up`. The Docker + Compose
install steps are shared with the BillRight scripts, which were tested on Amazon Linux 2023.

## 1. Launch the instance

- **Type:** t3.large (2 vCPU, 8 GB) or bigger. Smaller machines get a 4 GB swap file but train slowly.
- **Disk:** 25 GB or more. The image is about 3.2 GB; the build needs about 10 GB free.
- **Security group:** allow inbound TCP **8080** (dashboard), and **8081** if you want the API and Swagger.

## 2. Copy the scripts and run

```bash
# from your machine (use ubuntu@ on Ubuntu, ec2-user@ on Amazon Linux)
scp -i key.pem build_project.sh run_on_ec2.sh ec2-user@<public-ip>:~

# on the instance
GEMINI_API_KEY=your-key bash run_on_ec2.sh
```

Or clone this repo on the instance and run `bash clearauth/run_on_ec2.sh`.
If `GEMINI_API_KEY` is not set, the script asks for it (input is hidden).

The image build takes 5 to 10 minutes (Python packages and the embedding model). The
**first start** then cleans the data, trains the three models and builds the policy
index, which takes a few more minutes. The script waits for all of it and then prints:

```
Dashboard : http://<public-ip>:8080
REST API  : http://<public-ip>:8081/docs
```

Later starts are quick: the models and index are kept in Docker volumes.

## 3. Sign in

| User | Password | Role |
| --- | --- | --- |
| `maria` (also `james`, `leena`) | `11111111` | UM Nurse Reviewer |
| `carlos` | `22222222` | Intake Coordinator |
| `ravi` | `33333333` | Provider Services Representative |

These are seeded demo accounts.

## Day-to-day

Run these from the project folder, `~/clearauth-ai`:

| Task | Command |
| --- | --- |
| Stop | `docker compose down` |
| Start | `docker compose up -d` |
| Follow logs | `docker compose logs -f` |
| Status | `docker compose ps` |
| Rebuild after a code change | `docker compose up -d --build` |
| Reset all data (retrains on next start) | `docker compose down -v` |
| Run the offline checks on start | add `RUN_TESTS=1` to `.env`, then `docker compose up -d` |
| Recreate the code from scratch | `rm -rf ~/clearauth-ai && bash run_on_ec2.sh` |

Use `sudo docker ...` until you log in again (the script adds you to the `docker` group).

## Options

Set these as environment variables before `run_on_ec2.sh`. They are saved in `.env`,
which `docker compose` reads, so later `up`/`down` use the same values.

| Variable | Default | Purpose |
| --- | --- | --- |
| `GEMINI_API_KEY` | asked for | Gemini key (`.env` is mode 600) |
| `GEMINI_MODEL` | `gemini-3.1-flash-lite` | Model name |
| `APP_DIR` | `~/clearauth-ai` | Where the project is written |
| `DASHBOARD_PORT` | `8080` | Host port for the dashboard |
| `API_PORT` | `8081` | Host port for the REST API |
| `API_BIND` | `0.0.0.0` | Set `127.0.0.1` to keep the API private; then reach Swagger with `ssh -L 8081:127.0.0.1:8081 ec2-user@<ip>` and open http://localhost:8081/docs |

## Data that persists

| Volume | Holds |
| --- | --- |
| `clearauth_clearauth_database` | `clearauth.db` (users, reviews, decisions, agent runs, chat history, LLM call log), `checkpoint.db` (paused agent runs), the policy index |
| `clearauth_clearauth_output` | trained models and metrics |
| `clearauth_clearauth_processed` | cleaned training data |

## Troubleshooting

- **Page doesn't load:** check that the security group allows the port, and use `http://`, not `https://`.
- **"Only N GB free disk":** grow the EBS volume, then run the script again.
- **Container stopped:** the script prints the last 40 log lines. Check `docker compose logs`.
- **Reviews or letters fail:** the Gemini key or model name in `~/clearauth-ai/.env` is wrong. Fix it, then `docker compose up -d`.
- **Amazon Linux prints "legacy builder is deprecated":** harmless.
