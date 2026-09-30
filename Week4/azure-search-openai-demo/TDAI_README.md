# Week 4 — RAG Chatbot (TDAI Course)

A RAG (Retrieval Augmented Generation) chatbot that lets you chat with company documents using Azure OpenAI + Azure AI Search. The Azure infrastructure is pre-deployed by your trainer — you just run the app locally.

## Prerequisites

- Python 3.11+
- Node.js 18+
- [Azure CLI (`az`)](https://docs.microsoft.com/cli/azure/install-azure-cli)
- [Azure Developer CLI (`azd`)](https://aka.ms/install-azd)

**Windows quick install:**
```powershell
winget install Microsoft.AzureCLI
winget install Microsoft.Azd
```

---

## Quick Start (recommended)

Run the setup script once — it checks prerequisites, configures the environment, builds the frontend, and installs Python deps:

**Windows:**
```powershell
powershell -ExecutionPolicy Bypass -File student-setup.ps1
```

**Mac/Linux:**
```bash
bash student-setup.sh
```

Then follow the steps in [Running the app](#running-the-app) below.

---

## Setting up a Python virtual environment

The `.venv` folder is **not included in the repo** — you need to create it yourself. A virtual environment keeps the app's dependencies isolated from your system Python.

```bash
# From the azure-search-openai-demo folder
python -m venv .venv
```

Activate it:

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```
```bash
# Mac/Linux
source .venv/bin/activate
```

Install dependencies:

```bash
cd app/backend
pip install -r requirements.txt
```

You should see `(.venv)` in your terminal prompt once activated. **Always activate the venv before running the app.**

> If you skip the venv and get `No module named quart` when running the app, it means Python can't find the installed packages. Either activate the venv, or run `pip install -r app/backend/requirements.txt` from the `azure-search-openai-demo` folder.

---

## Running the app

Make sure your venv is active, then from `app/backend`:

**Windows (PowerShell):**
```powershell
cd app\backend
$env:AZURE_OPENAI_API_KEY_OVERRIDE="<provided by trainer>"
$env:AZURE_SEARCH_KEY_OVERRIDE="<provided by trainer>"
python -m quart --app main:app run --port 50505 --reload
```

**Mac/Linux:**
```bash
cd app/backend
AZURE_OPENAI_API_KEY_OVERRIDE="<provided by trainer>" \
AZURE_SEARCH_KEY_OVERRIDE="<provided by trainer>" \
python -m quart --app main:app run --port 50505 --reload
```

Open **http://localhost:50505** in your browser.

---

## Running from VS Code (easier)

VS Code makes it easy to manage the venv and open the browser automatically.

### 1. Install the Python extension

Search for **Python** (by Microsoft) in the Extensions panel (`Ctrl+Shift+X`) and install it.

### 2. Select your interpreter

Open the Command Palette (`Ctrl+Shift+P`) → **Python: Select Interpreter** → choose the `.venv` you created inside `azure-search-openai-demo`.

### 3. Open a terminal and run

VS Code's integrated terminal (`Ctrl+`` `) automatically activates the selected venv. Set your env vars and start the app:

```powershell
cd app\backend
$env:AZURE_OPENAI_API_KEY_OVERRIDE="<provided by trainer>"
$env:AZURE_SEARCH_KEY_OVERRIDE="<provided by trainer>"
python -m quart --app main:app run --port 50505 --reload
```

### 4. Open the app in VS Code's Simple Browser

Once the server starts, VS Code shows a **Ports** tab (bottom panel) with port `50505` listed. Click **Open in Browser** next to it, or:

- Open the Command Palette (`Ctrl+Shift+P`) → **Simple Browser: Show** → enter `http://localhost:50505`

This opens the chatbot directly inside VS Code so you don't need to leave the editor.

---

## Manual Setup (if the setup script doesn't work)

### 1. Configure the environment

```bash
mkdir -p .azure/tdai-rag-chatbot
cp .env.example .azure/tdai-rag-chatbot/.env
```

Fill in the values your trainer provides, then:

```bash
azd env select tdai-rag-chatbot
```

### 2. Build the frontend

```bash
cd app/frontend
npm install
npm run build
```

### 3. Create venv and install Python dependencies

```bash
python -m venv .venv
# Activate (Windows): .venv\Scripts\Activate.ps1
# Activate (Mac/Linux): source .venv/bin/activate
cd app/backend
pip install -r requirements.txt
```

---

## Try asking

- "What are the employee benefits?"
- "What is the annual leave policy?"
- "Summarise the health insurance options"
- "What does the Northwind Health Plus plan cover?"

---

## How it works

```
Your browser
     │
     ▼
React frontend  (localhost:50505)
     │
     ▼
Python/Quart backend  (localhost:50505/api)
     │
     ├──► Azure AI Search  ──►  Azure Blob Storage
     │      (retrieve relevant       (source PDFs)
     │       document chunks)
     │
     └──► Azure OpenAI GPT-4.1-mini
            (generate answer using retrieved context)
```

**RAG in a nutshell:** Instead of sending your question directly to the LLM, the app first searches a pre-indexed knowledge base for the most relevant document passages, then sends those passages *plus* your question to the LLM. This grounds the answer in your actual documents and reduces hallucination.

---

## Code worth exploring

| File | What it shows |
|---|---|
| `app/backend/approaches/chatreadretrieveread.py` | The full RAG pipeline — retrieve then read |
| `app/backend/app.py` | How the backend is wired up (auth, search client, OpenAI client) |
| `app/frontend/src/` | React chat UI |
| `app/backend/prepdocslib/` | How documents are chunked, embedded, and indexed |

---

## Want to deploy your own version? (optional, personal Azure account)

If you have your own Azure account and want to deploy the full stack yourself, here's exactly what was done to set this up — you can replicate it.

### 1. Deploy all Azure resources with `azd up`

`azd` (Azure Developer CLI) reads the `azure.yaml` and `infra/` Bicep templates in the repo and provisions everything in one command:

```bash
azd auth login
azd env new my-rag-demo       # give your environment a name
azd up                        # provisions resources + deploys the app to Azure
```

`azd up` will:
- Create an Azure OpenAI resource with GPT + embedding deployments
- Create an Azure AI Search service (Standard tier)
- Create a Storage account and upload the sample PDFs from `data/`
- Index the documents into AI Search (chunking + embeddings via Document Intelligence)
- Deploy the backend as a Container App and frontend as a static site
- Output the live URL when done

This takes ~15 minutes and costs money while running. Use a free trial or student subscription.

### 2. Index documents (prepdocs)

`azd up` runs indexing automatically, but if you add new PDFs to `data/` later you can re-index manually:

```bash
# Mac/Linux
./scripts/prepdocs.sh

# Windows
./scripts/prepdocs.ps1
```

This script:
1. Reads each PDF using Azure Document Intelligence (layout-aware chunking)
2. Generates vector embeddings for each chunk using your OpenAI embeddings deployment
3. Uploads chunks + embeddings into your AI Search index

Run with `--verbose` to see exactly what's happening chunk by chunk.

### 3. Tear everything down with `azd down`

When you're done experimenting, delete all provisioned resources to stop billing:

```bash
azd down
```

This deletes the resource group and everything inside it. Your local code is untouched. Think of it as the exact opposite of `azd up` — always run it when you're done with a demo environment to avoid surprise charges.

### 4. Run locally against your own deployed resources

Once `azd up` has run, you can also run the app locally pointing at your own resources:

```bash
azd env get-values   # shows all your resource names and endpoints
cd app/backend
python -m quart --app main:app run --port 50505 --reload
```

No key overrides needed — `azd auth login` handles credentials automatically when running against your own deployment.
