#!/usr/bin/env bash
# =============================================================================
# BillRight AI: install everything on a fresh EC2 instance and run it.
#
#   GEMINI_API_KEY=xxxx bash run_on_ec2.sh        (or run it and paste the key)
#
# Works on Ubuntu 22.04/24.04 and Amazon Linux 2023. Safe to re-run: it rebuilds
# the image and recreates the container, keeping the data volumes.
#
# Steps
#   1. install Docker + the Compose plugin, start Docker, let this user run it
#   2. add swap if the machine has under 6 GB RAM (model training + torch)
#   3. recreate the project with build_project.sh (if not already there)
#   4. write .env (Gemini key, model, ports)
#   5. docker build, then docker compose up -d
#   6. wait until healthy (first start trains the models + builds the index)
#
# Afterwards manage it with Compose from the project folder:
#   cd ~/billright-ai && docker compose down        (stop)
#   cd ~/billright-ai && docker compose up -d       (start)
#
# Instance: t3.large (2 vCPU, 8 GB) or bigger, 25 GB+ disk. Open inbound TCP
# 8080 (and 8081 if you want the API/Swagger) in the security group.
# =============================================================================
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${APP_DIR:-$HOME/billright-ai}"
IMAGE="billright-ai:latest"
CONTAINER="billright-ai"
DASHBOARD_PORT="${DASHBOARD_PORT:-8080}"
API_PORT="${API_PORT:-8081}"
API_BIND="${API_BIND:-0.0.0.0}"
COMPOSE_VERSION="v2.29.7"

log()  { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
die()  { printf '\033[1;31mERROR: %s\033[0m\n' "$*" >&2; exit 1; }
SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"

# ----------------------------------------------------------------- 1. Docker
install_docker() {
    . /etc/os-release
    case "$ID" in
        ubuntu|debian)
            log "Installing Docker (apt, $PRETTY_NAME)"
            $SUDO apt-get update -y
            $SUDO apt-get install -y ca-certificates curl
            curl -fsSL https://get.docker.com | $SUDO sh      # includes the Compose plugin
            ;;
        amzn|rhel|centos|fedora|rocky|almalinux)
            log "Installing Docker (dnf/yum, $PRETTY_NAME)"
            if command -v dnf >/dev/null 2>&1; then PM=dnf; else PM=yum; fi
            $SUDO $PM install -y docker curl-minimal 2>/dev/null || $SUDO $PM install -y docker curl
            ;;
        *) die "Unsupported OS '$ID'. Install Docker yourself, then re-run." ;;
    esac
}

if ! command -v docker >/dev/null 2>&1; then
    install_docker
else
    log "Docker already installed: $(docker --version)"
fi

if command -v systemctl >/dev/null 2>&1 && [ -d /run/systemd/system ]; then
    $SUDO systemctl enable --now docker >/dev/null
fi

# Use sudo for docker until this user's group membership takes effect (next login).
if docker info >/dev/null 2>&1; then
    DOCKER="docker"
else
    $SUDO usermod -aG docker "$(id -un)" 2>/dev/null || true
    DOCKER="$SUDO docker"
    $DOCKER info >/dev/null 2>&1 || die "Docker daemon is not running."
fi

# Compose plugin (Amazon Linux's docker package does not ship it).
if ! $DOCKER compose version >/dev/null 2>&1; then
    log "Installing the Docker Compose plugin ($COMPOSE_VERSION)"
    ARCH="$(uname -m)"; [ "$ARCH" = "arm64" ] && ARCH="aarch64"
    $SUDO mkdir -p /usr/local/lib/docker/cli-plugins
    $SUDO curl -fsSL -o /usr/local/lib/docker/cli-plugins/docker-compose \
        "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-linux-${ARCH}"
    $SUDO chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
    $DOCKER compose version >/dev/null 2>&1 || die "Docker Compose plugin did not install."
fi
log "$($DOCKER compose version)"

# ----------------------------------------------------------------- 2. swap
MEM_MB=$(awk '/MemTotal/ {print int($2/1024)}' /proc/meminfo)
add_swap() {
    $SUDO fallocate -l 4G /swapfile 2>/dev/null || $SUDO dd if=/dev/zero of=/swapfile bs=1M count=4096
    $SUDO chmod 600 /swapfile
    $SUDO mkswap /swapfile >/dev/null
    $SUDO swapon /swapfile
    grep -q '^/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' | $SUDO tee -a /etc/fstab >/dev/null
}
if [ "$MEM_MB" -lt 6000 ] && ! swapon --show 2>/dev/null | grep -q .; then
    log "Only ${MEM_MB} MB RAM: adding a 4 GB swap file"
    add_swap 2>/dev/null || echo "Could not add swap (continuing; training may be slow or run out of memory)."
fi

FREE_GB=$(df -Pk "$HOME" | awk 'NR==2 {print int($4/1024/1024)}')
[ "$FREE_GB" -lt 10 ] && die "Only ${FREE_GB} GB free disk; the image needs ~10 GB to build. Grow the EBS volume."

# ----------------------------------------------------------------- 3. project
if [ ! -f "$APP_DIR/Dockerfile" ]; then
    [ -f "$HERE/build_project.sh" ] || die "build_project.sh not found next to this script and $APP_DIR has no project."
    log "Recreating the project in $APP_DIR"
    bash "$HERE/build_project.sh" "$APP_DIR"
else
    log "Project already present in $APP_DIR (delete it to recreate from build_project.sh)"
fi
cd "$APP_DIR"

# ----------------------------------------------------------------- 4. .env
env_value() { [ -f .env ] && grep -E "^$1=" .env | tail -1 | cut -d= -f2- || true; }
[ -n "${GEMINI_API_KEY:-}" ] || GEMINI_API_KEY="$(env_value GEMINI_API_KEY)"
[ -n "${GEMINI_MODEL:-}" ]   || GEMINI_MODEL="$(env_value GEMINI_MODEL)"
if [ -z "${GEMINI_API_KEY:-}" ] || [ "$GEMINI_API_KEY" = "your-gemini-api-key" ]; then
    [ -t 0 ] || die "Set GEMINI_API_KEY (e.g. GEMINI_API_KEY=xxx bash run_on_ec2.sh)."
    read -r -s -p "Gemini API key: " GEMINI_API_KEY; echo
fi
[ -n "$GEMINI_API_KEY" ] || die "No Gemini API key given."
umask 077
cat > .env <<EOF
GEMINI_API_KEY=${GEMINI_API_KEY}
GEMINI_MODEL=${GEMINI_MODEL:-gemini-3.1-flash-lite}
DASHBOARD_PORT=${DASHBOARD_PORT}
API_PORT=${API_PORT}
API_BIND=${API_BIND}
EOF
umask 022

# ----------------------------------------------------------------- 5. build + run
log "Building the image (installs Python packages: ~5-10 min the first time)"
$DOCKER build -t "$IMAGE" .

log "Starting with docker compose"
$DOCKER rm -f "$CONTAINER" >/dev/null 2>&1 || true    # a container left by an older run
$DOCKER compose up -d --no-build --force-recreate

# ----------------------------------------------------------------- 6. wait
echo "Waiting for the services. The first start cleans the data, trains the models and"
printf 'builds the document index (~5-15 min)'
STATUS="starting"
for _ in $(seq 1 240); do
    STATUS="$($DOCKER inspect -f '{{.State.Health.Status}}' "$CONTAINER" 2>/dev/null || echo gone)"
    [ "$STATUS" = "healthy" ] && break
    if [ "$STATUS" = "gone" ] || [ "$($DOCKER inspect -f '{{.State.Running}}' "$CONTAINER")" != "true" ]; then
        echo; $DOCKER compose logs --tail 40; die "Container stopped. Logs above."
    fi
    printf '.'; sleep 5
done
echo
[ "$STATUS" = "healthy" ] || { $DOCKER compose logs --tail 40; die "Not healthy after 20 minutes."; }

# Public address from instance metadata (IMDSv2), falling back to the local IP.
TOKEN="$(curl -s -m 2 -X PUT http://169.254.169.254/latest/api/token \
    -H 'X-aws-ec2-metadata-token-ttl-seconds: 60' || true)"
HOST="$(curl -s -m 2 -H "X-aws-ec2-metadata-token: $TOKEN" \
    http://169.254.169.254/latest/meta-data/public-ipv4 || true)"
[ -n "$HOST" ] || HOST="$(hostname -I 2>/dev/null | awk '{print $1}')"

log "BillRight AI is running"
cat <<EOF
  Dashboard : http://${HOST}:${DASHBOARD_PORT}
  REST API  : http://${HOST}:${API_PORT}/docs
  Sign in   : fiona / 11111111 (Revenue Controller), hamish / 22222222 (Billing Analyst),
              megan / 33333333 (Contact Centre Agent)

  From $APP_DIR:
  Logs      : $DOCKER compose logs -f
  Stop      : $DOCKER compose down
  Start     : $DOCKER compose up -d
  Redeploy  : bash $HERE/run_on_ec2.sh
  Reset data: $DOCKER compose down -v

  Security group must allow inbound TCP ${DASHBOARD_PORT} (and ${API_PORT}).
EOF
