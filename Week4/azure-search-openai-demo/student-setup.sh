#!/usr/bin/env bash
# =============================================================
# TDAI RAG Chatbot — Student Local Setup Script
# Run this once to configure and run the app locally.
# Prerequisites: Python 3.11+, Node.js, azd, az CLI
# =============================================================
set -e

# ── Instructor-configured values (do not change) ─────────────
SUBSCRIPTION_ID=""
TENANT_ID=""
OPENAI_SERVICE=""
OPENAI_ENDPOINT=""
STORAGE_ACCOUNT=""
SEARCH_SERVICE=""
SEARCH_IDENTITY_ID=""
OPENAI_KEY=""
SEARCH_KEY=""
# ─────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_DIR="$SCRIPT_DIR/.azure/tdai-rag-chatbot"
ENV_FILE="$ENV_DIR/.env"

echo ""
echo "=== TDAI RAG Chatbot — Student Setup ==="
echo ""

# ── Step 1: Prerequisites check ──────────────────────────────
check_cmd() {
  if ! command -v "$1" &>/dev/null; then
    echo "ERROR: '$1' not found. Please install it and re-run."
    echo "  $2"
    exit 1
  fi
}

echo "[1/6] Checking prerequisites..."
check_cmd az    "https://docs.microsoft.com/cli/azure/install-azure-cli"
check_cmd azd   "https://aka.ms/install-azd"
check_cmd python3 "https://www.python.org/downloads/"
check_cmd node  "https://nodejs.org/"
echo "      All prerequisites found."

# ── Step 2: Create env folder and populate .env ──────────────
echo "[2/6] Configuring environment..."
mkdir -p "$ENV_DIR"

if [ ! -f "$SCRIPT_DIR/.env.example" ]; then
  echo "ERROR: .env.example not found in $SCRIPT_DIR"
  exit 1
fi

cp "$SCRIPT_DIR/.env.example" "$ENV_FILE"

# Fill in the blank values
sed -i "s|AZURE_SUBSCRIPTION_ID=\"\"|AZURE_SUBSCRIPTION_ID=\"$SUBSCRIPTION_ID\"|" "$ENV_FILE"
sed -i "s|AZURE_TENANT_ID=\"\"|AZURE_TENANT_ID=\"$TENANT_ID\"|" "$ENV_FILE"
sed -i "s|AZURE_OPENAI_SERVICE=\"\"|AZURE_OPENAI_SERVICE=\"$OPENAI_SERVICE\"|" "$ENV_FILE"
sed -i "s|AZURE_OPENAI_ENDPOINT=\"\"|AZURE_OPENAI_ENDPOINT=\"$OPENAI_ENDPOINT\"|" "$ENV_FILE"
sed -i "s|AZURE_STORAGE_ACCOUNT=\"\"|AZURE_STORAGE_ACCOUNT=\"$STORAGE_ACCOUNT\"|" "$ENV_FILE"
sed -i "s|AZURE_SEARCH_USER_ASSIGNED_IDENTITY_RESOURCE_ID=\"\"|AZURE_SEARCH_USER_ASSIGNED_IDENTITY_RESOURCE_ID=\"$SEARCH_IDENTITY_ID\"|" "$ENV_FILE"

echo "      .env written to $ENV_FILE"

# ── Step 3: Register azd environment ─────────────────────────
echo "[3/6] Registering azd environment..."
cd "$SCRIPT_DIR"
azd env select tdai-rag-chatbot 2>/dev/null || azd env new tdai-rag-chatbot 2>/dev/null || true
echo "      azd environment set to 'tdai-rag-chatbot'."

# ── Step 4: Azure login ───────────────────────────────────────
echo "[4/6] Logging in to Azure..."
echo "      A browser window will open — sign in with your university/course account."
az login --tenant "$TENANT_ID" --output none
echo "      Logged in."

# ── Step 5: Build frontend ────────────────────────────────────
echo "[5/6] Building frontend..."
cd "$SCRIPT_DIR/app/frontend"
npm install --silent
npm run build --silent
echo "      Frontend built."

# ── Step 6: Install Python dependencies ──────────────────────
echo "[6/6] Installing Python dependencies..."
cd "$SCRIPT_DIR/app/backend"
pip install -r requirements.txt -q
echo "      Python dependencies installed."

# ── Done ──────────────────────────────────────────────────────
echo ""
echo "=== Setup complete! ==="
echo ""
echo "To run the app:"
echo "  cd app/backend"
echo "  AZURE_OPENAI_API_KEY_OVERRIDE=\"$OPENAI_KEY\" \\"
echo "  AZURE_SEARCH_KEY_OVERRIDE=\"$SEARCH_KEY\" \\"
echo "  python -m quart --app main:app run --port 50505 --reload"
echo ""
echo "Then open: http://localhost:50505"
echo ""
