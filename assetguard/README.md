# AssetGuard AI on EC2

Two scripts that deploy AssetGuard AI (predictive maintenance: Streamlit dashboard,
REST API, manual chat backed by Gemini) to a fresh EC2 instance with Docker.

| Script | What it does |
| --- | --- |
| `build_project.sh` | Writes the whole project (code, Dockerfile, raw data, manuals) into a folder and checks every file's SHA-256. |
| `run_on_ec2.sh` | Installs Docker, adds swap on small machines, runs `build_project.sh`, writes `.env`, builds the image and starts the container. |

Tested on Ubuntu 24.04 (full run) and Amazon Linux 2023 (Docker install step).

## 1. Launch the instance

- **Type:** t3.large (2 vCPU, 8 GB) or bigger. Smaller machines get a 4 GB swap file but train slowly.
- **Disk:** 25 GB or more. The image build needs about 10 GB free.
- **Security group:** allow inbound TCP **8080** (dashboard), and **8081** if you want the API and Swagger.

## 2. Copy the scripts and run

```bash
# from your machine (use ubuntu@ on Ubuntu, ec2-user@ on Amazon Linux)
scp -i key.pem build_project.sh run_on_ec2.sh ec2-user@<public-ip>:~

# on the instance
GEMINI_API_KEY=your-key bash run_on_ec2.sh
```

Or clone this repo on the instance and run `bash assetguard/run_on_ec2.sh`.
If `GEMINI_API_KEY` is not set, the script asks for it (input is hidden).

The first build takes 10 to 20 minutes, because it installs the packages, trains the
models and builds the manual index. When it finishes, it prints:

```
Dashboard : http://<public-ip>:8080
REST API  : http://<public-ip>:8081/docs
```

## 3. Sign in

The demo accounts are printed in the container logs:

```bash
sudo docker logs assetguard-ai 2>&1 | grep -A8 'Accounts you can sign in'
```

## Day-to-day

| Task | Command |
| --- | --- |
| Follow logs | `sudo docker logs -f assetguard-ai` |
| Restart | `sudo docker restart assetguard-ai` |
| Redeploy (rebuild image, keep data) | `bash run_on_ec2.sh` |
| Reset all data | `sudo docker rm -f assetguard-ai && sudo docker volume rm assetguard-state` |
| Recreate the code from scratch | `rm -rf ~/assetguard-ai && bash run_on_ec2.sh` |

`sudo` is only needed until you log in again (the script adds you to the `docker` group).

## Options

Set these as environment variables before `run_on_ec2.sh`:

| Variable | Default | Purpose |
| --- | --- | --- |
| `GEMINI_API_KEY` | asked for | Gemini key, saved to `.env` (mode 600) |
| `GEMINI_MODEL` | `gemini-3.1-flash-lite` | Model name |
| `APP_DIR` | `~/assetguard-ai` | Where the project is written |
| `DASHBOARD_PORT` | `8080` | Host port for the dashboard |
| `API_PORT` | `8081` | Host port for the REST API |

Users, work orders, reviews and chat history live in the `assetguard-state` Docker
volume, so they survive restarts and redeploys.

## Troubleshooting

- **Page doesn't load:** check that the security group allows the port, and use `http://`, not `https://`.
- **"Only N GB free disk":** grow the EBS volume, then run the script again.
- **Container stopped:** the script prints the last 40 log lines. A missing or wrong Gemini key is the usual cause.
- **Amazon Linux prints "legacy builder is deprecated":** harmless.
