#!/usr/bin/env bash
# =============================================================================
# AssetGuard AI: install everything on a fresh EC2 instance and run it.
#
#   GEMINI_API_KEY=xxxx bash run_on_ec2.sh        (or run it and paste the key)
#
# Works on Ubuntu 22.04/24.04 and Amazon Linux 2023. Safe to re-run: it rebuilds
# the image and replaces the container, keeping the data volume.
#
# Steps
#   1. install Docker (and git/curl), start it, let this user run it
#   2. add swap if the machine has under 6 GB RAM (model training + torch)
#   3. recreate the project with build_project.sh (if not already there)
#   4. write .env with the Gemini key
#   5. docker build (trains models + builds the manual index on first build)
#   6. run the container: dashboard :8080, REST API :8081, data in a volume
#
# Instance: t3.large (2 vCPU, 8 GB) or bigger, 25 GB+ disk. Open inbound TCP
# 8080 (and 8081 if you want the API/Swagger) in the security group.
# =============================================================================
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${APP_DIR:-$HOME/assetguard-ai}"
IMAGE="${IMAGE:-assetguard-ai:latest}"
CONTAINER="${CONTAINER:-assetguard-ai}"
VOLUME="${VOLUME:-assetguard-state}"
DASHBOARD_PORT="${DASHBOARD_PORT:-8080}"
API_PORT="${API_PORT:-8081}"

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
            curl -fsSL https://get.docker.com | $SUDO sh
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
if [ -z "${GEMINI_API_KEY:-}" ] && [ -f .env ]; then
    GEMINI_API_KEY="$(grep -E '^GEMINI_API_KEY=' .env | cut -d= -f2- || true)"
fi
if [ -z "${GEMINI_API_KEY:-}" ] || [ "$GEMINI_API_KEY" = "your-gemini-api-key" ]; then
    [ -t 0 ] || die "Set GEMINI_API_KEY (e.g. GEMINI_API_KEY=xxx bash run_on_ec2.sh)."
    read -r -s -p "Gemini API key: " GEMINI_API_KEY; echo
fi
[ -n "$GEMINI_API_KEY" ] || die "No Gemini API key given."
umask 077
cat > .env <<EOF
GEMINI_API_KEY=${GEMINI_API_KEY}
GEMINI_MODEL=${GEMINI_MODEL:-gemini-3.1-flash-lite}
EOF
umask 022

# ----------------------------------------------------------------- 5. build
log "Building the image (first build installs packages and trains the models: ~10-20 min)"
$DOCKER build -t "$IMAGE" .

# ----------------------------------------------------------------- 6. run
log "Starting the container"
$DOCKER rm -f "$CONTAINER" >/dev/null 2>&1 || true
$DOCKER volume create "$VOLUME" >/dev/null
$DOCKER run -d --name "$CONTAINER" --restart unless-stopped \
    --env-file .env \
    -p "${DASHBOARD_PORT}:8080" -p "${API_PORT}:8081" \
    -v "${VOLUME}:/app/state" \
    "$IMAGE" >/dev/null

printf 'Waiting for the services'
for _ in $(seq 1 60); do
    STATUS="$($DOCKER inspect -f '{{.State.Health.Status}}' "$CONTAINER" 2>/dev/null || echo gone)"
    [ "$STATUS" = "healthy" ] && break
    [ "$STATUS" = "gone" ] || [ "$($DOCKER inspect -f '{{.State.Running}}' "$CONTAINER")" != "true" ] && {
        echo; $DOCKER logs --tail 40 "$CONTAINER"; die "Container stopped. Logs above."; }
    printf '.'; sleep 5
done
echo
[ "$STATUS" = "healthy" ] || { $DOCKER logs --tail 40 "$CONTAINER"; die "Not healthy after 5 minutes."; }

# Public address from instance metadata (IMDSv2), falling back to the local IP.
TOKEN="$(curl -s -m 2 -X PUT http://169.254.169.254/latest/api/token \
    -H 'X-aws-ec2-metadata-token-ttl-seconds: 60' || true)"
HOST="$(curl -s -m 2 -H "X-aws-ec2-metadata-token: $TOKEN" \
    http://169.254.169.254/latest/meta-data/public-ipv4 || true)"
[ -n "$HOST" ] || HOST="$(hostname -I 2>/dev/null | awk '{print $1}')"

log "AssetGuard AI is running"
cat <<EOF
  Dashboard : http://${HOST}:${DASHBOARD_PORT}
  REST API  : http://${HOST}:${API_PORT}/docs
  Sign-in accounts: $DOCKER logs $CONTAINER 2>&1 | grep -A8 'Accounts you can sign in'

  Logs      : $DOCKER logs -f $CONTAINER
  Restart   : $DOCKER restart $CONTAINER
  Redeploy  : bash $HERE/run_on_ec2.sh
  Reset data: $DOCKER rm -f $CONTAINER && $DOCKER volume rm $VOLUME

  Security group must allow inbound TCP ${DASHBOARD_PORT} (and ${API_PORT}).
EOF
