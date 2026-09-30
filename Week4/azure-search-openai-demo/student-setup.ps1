# =============================================================
# TDAI RAG Chatbot — Student Local Setup Script (Windows)
# Run this once to configure and run the app locally.
# Prerequisites: Python 3.11+, Node.js, azd, az CLI
#
# Usage: Right-click > "Run with PowerShell"
#   or:  powershell -ExecutionPolicy Bypass -File student-setup.ps1
# =============================================================

# ── Instructor-configured values (do not change) ─────────────
$CHAT_DEPLOYMENT   = "gpt-4.1-mini-256985"
$CHAT_MODEL        = "gpt-4.1-mini"
$EMB_DEPLOYMENT    = "text-embedding-3-large-233097"
$EMB_MODEL         = "text-embedding-3-large"
$EMB_DIMENSIONS    = "3072"

$SUBSCRIPTION_ID   = "d6a95651-f1ac-429d-8a56-996f90f37c43"
$TENANT_ID         = "3591ff50-2b90-4b13-b7e0-246e055ac456"
$OPENAI_SERVICE    = "tdai-foundry"
$OPENAI_ENDPOINT   = "https://tdai-foundry.cognitiveservices.azure.com/"
$STORAGE_ACCOUNT   = "tdaistrgacnt"
$SEARCH_SERVICE    = "tdai-rag-search"
$SEARCH_IDENTITY   = "/subscriptions/d6a95651-f1ac-429d-8a56-996f90f37c43/resourcegroups/tdai-learning/providers/Microsoft.ManagedIdentity/userAssignedIdentities/tdai-rag-search-identity"
# ─────────────────────────────────────────────────────────────

$ErrorActionPreference = "Stop"
$SCRIPT_DIR = $PSScriptRoot
$ENV_DIR    = Join-Path $SCRIPT_DIR ".azure\tdai-rag-chatbot"
$ENV_FILE   = Join-Path $ENV_DIR ".env"

Write-Host ""
Write-Host "=== TDAI RAG Chatbot — Student Setup ===" -ForegroundColor Cyan
Write-Host ""

# ── Step 1: Prerequisites check ──────────────────────────────
Write-Host "[1/6] Checking prerequisites..." -ForegroundColor Yellow

$missing = @()
if (-not (Get-Command az    -ErrorAction SilentlyContinue)) { $missing += "az CLI  -> https://docs.microsoft.com/cli/azure/install-azure-cli" }
if (-not (Get-Command azd   -ErrorAction SilentlyContinue)) { $missing += "azd     -> https://aka.ms/install-azd" }
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { $missing += "python  -> https://www.python.org/downloads/" }
if (-not (Get-Command node  -ErrorAction SilentlyContinue)) { $missing += "node    -> https://nodejs.org/" }

if ($missing.Count -gt 0) {
    Write-Host "ERROR: Missing prerequisites:" -ForegroundColor Red
    $missing | ForEach-Object { Write-Host "  $_" }
    exit 1
}
Write-Host "      All prerequisites found." -ForegroundColor Green

# ── Step 2: Create env folder and populate .env ──────────────
Write-Host "[2/6] Configuring environment..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $ENV_DIR | Out-Null

$exampleFile = Join-Path $SCRIPT_DIR ".env.example"
if (-not (Test-Path $exampleFile)) {
    Write-Host "ERROR: .env.example not found in $SCRIPT_DIR" -ForegroundColor Red
    exit 1
}

# Read explicitly as UTF-8: Windows PowerShell 5.1 would otherwise decode it as ANSI and garble non-ASCII characters
$content = [System.IO.File]::ReadAllText($exampleFile, [System.Text.UTF8Encoding]::new($false))

$content = $content -replace '(?m)^AZURE_SUBSCRIPTION_ID=.*$',                           "AZURE_SUBSCRIPTION_ID=`"$SUBSCRIPTION_ID`""
$content = $content -replace '(?m)^AZURE_TENANT_ID=.*$',                                 "AZURE_TENANT_ID=`"$TENANT_ID`""
$content = $content -replace '(?m)^AZURE_OPENAI_SERVICE=.*$',                            "AZURE_OPENAI_SERVICE=`"$OPENAI_SERVICE`""
$content = $content -replace '(?m)^AZURE_OPENAI_ENDPOINT=.*$',                           "AZURE_OPENAI_ENDPOINT=`"$OPENAI_ENDPOINT`""
$content = $content -replace '(?m)^AZURE_STORAGE_ACCOUNT=.*$',                           "AZURE_STORAGE_ACCOUNT=`"$STORAGE_ACCOUNT`""
$content = $content -replace '(?m)^AZURE_SEARCH_SERVICE=.*$',                            "AZURE_SEARCH_SERVICE=`"$SEARCH_SERVICE`""
$content = $content -replace '(?m)^AZURE_SEARCH_USER_ASSIGNED_IDENTITY_RESOURCE_ID=.*$', "AZURE_SEARCH_USER_ASSIGNED_IDENTITY_RESOURCE_ID=`"$SEARCH_IDENTITY`""

$content = $content -replace '(?m)^AZURE_OPENAI_CHATGPT_DEPLOYMENT=.*$', "AZURE_OPENAI_CHATGPT_DEPLOYMENT=`"$CHAT_DEPLOYMENT`""
$content = $content -replace '(?m)^AZURE_OPENAI_CHATGPT_MODEL=.*$',      "AZURE_OPENAI_CHATGPT_MODEL=`"$CHAT_MODEL`""
$content = $content -replace '(?m)^AZURE_OPENAI_EMB_DEPLOYMENT=.*$',     "AZURE_OPENAI_EMB_DEPLOYMENT=`"$EMB_DEPLOYMENT`""
$content = $content -replace '(?m)^AZURE_OPENAI_EMB_MODEL_NAME=.*$',     "AZURE_OPENAI_EMB_MODEL_NAME=`"$EMB_MODEL`""
$content = $content -replace '(?m)^AZURE_OPENAI_EMB_DIMENSIONS=.*$',     "AZURE_OPENAI_EMB_DIMENSIONS=`"$EMB_DIMENSIONS`""

# Write UTF-8 *without* a BOM: azd rejects a .env file that starts with one ("unexpected character" error)
[System.IO.File]::WriteAllText($ENV_FILE, $content, [System.Text.UTF8Encoding]::new($false))

Write-Host "      .env written to $ENV_FILE" -ForegroundColor Green

# ── Step 3: Register azd environment ─────────────────────────
Write-Host "[3/6] Registering azd environment..." -ForegroundColor Yellow
Set-Location $SCRIPT_DIR
# azd prints update notices to stderr; under "Stop", Windows PowerShell 5.1 treats redirected stderr as a fatal error
$env:AZD_SKIP_UPDATE_CHECK = "true"
$ErrorActionPreference = "Continue"
azd env select tdai-rag-chatbot 2>$null
if ($LASTEXITCODE -ne 0) { azd env new tdai-rag-chatbot }
$azdExit = $LASTEXITCODE
$ErrorActionPreference = "Stop"
if ($azdExit -ne 0) {
    Write-Host "ERROR: Could not select the azd environment 'tdai-rag-chatbot'. Run 'azd env list' to check." -ForegroundColor Red
    exit 1
}
Write-Host "      azd environment set to 'tdai-rag-chatbot'." -ForegroundColor Green

# ── Step 4: Azure login ───────────────────────────────────────
Write-Host "[4/6] Logging in to Azure..." -ForegroundColor Yellow
Write-Host "      A browser window will open — sign in with your course account."
az login --tenant $TENANT_ID --output none
Write-Host "      Logged in." -ForegroundColor Green

# ── Step 5: Build frontend ────────────────────────────────────
Write-Host "[5/6] Building frontend..." -ForegroundColor Yellow
Set-Location (Join-Path $SCRIPT_DIR "app\frontend")
npm install --silent
npm run build --silent
Write-Host "      Frontend built." -ForegroundColor Green

# ── Step 6: Install Python dependencies ──────────────────────
Write-Host "[6/6] Installing Python dependencies..." -ForegroundColor Yellow
Set-Location (Join-Path $SCRIPT_DIR "app\backend")
pip install -r requirements.txt -q
Write-Host "      Python dependencies installed." -ForegroundColor Green

# ── Done ──────────────────────────────────────────────────────
# ── Done ──────────────────────────────────────────────────────
Write-Host ''
Write-Host '=== Setup complete! ===' -ForegroundColor Cyan
Write-Host ''
Write-Host 'To run the app, open a new terminal and run:' -ForegroundColor White
Write-Host ''
Write-Host '  cd app\backend' -ForegroundColor Yellow
Write-Host '  $env:AZURE_OPENAI_API_KEY_OVERRIDE="<provided by trainer>"' -ForegroundColor Yellow
Write-Host '  $env:AZURE_SEARCH_KEY_OVERRIDE="<provided by trainer>"' -ForegroundColor Yellow
Write-Host '  python -m quart --app main:app run --port 50505 --reload' -ForegroundColor Yellow
Write-Host ''
Write-Host 'Then open: http://localhost:50505' -ForegroundColor Green
Write-Host ''
