# Week 4 — RAG (Retrieval Augmented Generation)

The main demo for Week 4 is the **azure-search-openai-demo**, located at:

```
AI-Engineering-TDAI/
└── azure-search-openai-demo/   ← main demo is here
    └── TDAI_README.md          ← student setup instructions
```

## What this week covers

- What RAG is and why it matters
- Azure AI Search: indexing, chunking, vector embeddings
- Azure OpenAI: chat completions with retrieved context
- Running a full RAG chatbot locally against shared Azure resources

## Quick start (students)

1. Open a terminal in `azure-search-openai-demo/`
2. Run the setup script:
   - **Windows:** `powershell -ExecutionPolicy Bypass -File student-setup.ps1`
   - **Mac/Linux:** `bash student-setup.sh`
3. Start the app:
   ```powershell
   # Windows
   cd app\backend
   $env:AZURE_OPENAI_API_KEY_OVERRIDE="<provided by trainer>"
   $env:AZURE_SEARCH_KEY_OVERRIDE="<provided by trainer>"
   python -m quart --app main:app run --port 50505 --reload
   ```
4. Open [http://localhost:50505](http://localhost:50505)

Full setup instructions: [`azure-search-openai-demo/TDAI_README.md`](../azure-search-openai-demo/TDAI_README.md)

---

## Python virtual environment

The `.venv` folder is **not included in the repo** — you need to create it. From the `azure-search-openai-demo/` folder:

```bash
python -m venv .venv
```

Activate it:

```powershell
# Windows
.venv\Scripts\Activate.ps1
```
```bash
# Mac/Linux
source .venv/bin/activate
```

Then install dependencies:

```bash
cd app/backend
pip install -r requirements.txt
```

> If you get `No module named quart` when running the app, your venv isn't active or packages weren't installed into it. Activate the venv and re-run `pip install -r requirements.txt`.

---

## Running from VS Code (easier)

### 1. Install the Python extension
Search for **Python** (by Microsoft) in the Extensions panel (`Ctrl+Shift+X`).

### 2. Select your interpreter
`Ctrl+Shift+P` → **Python: Select Interpreter** → pick the `.venv` inside `azure-search-openai-demo/`.

### 3. Run from the integrated terminal
VS Code's terminal (`Ctrl+`` `) auto-activates the selected venv:

```powershell
cd app\backend
$env:AZURE_OPENAI_API_KEY_OVERRIDE="<provided by trainer>"
$env:AZURE_SEARCH_KEY_OVERRIDE="<provided by trainer>"
python -m quart --app main:app run --port 50505 --reload
```

### 4. Open in VS Code's Simple Browser
Once the server starts, VS Code shows a **Ports** tab (bottom panel) — click **Open in Browser** next to port `50505`. Or: `Ctrl+Shift+P` → **Simple Browser: Show** → `http://localhost:50505`.

---

## Azure Resources (shared, managed by instructor)

| Resource | Name | Region |
|---|---|---|
| Azure OpenAI | `tdai-foundry` | Australia East |
| Azure AI Search | `tdai-rag-search` | Australia East |
| Azure Blob Storage | `tdaistrgacnt` | East US |

> All resources are pre-deployed — you do not need your own Azure subscription to run the demo. The setup script and keys are provided by your trainer.

---

## Architecture

```
Your browser
      │
      ▼
React frontend  (localhost:50505)
      │
      ▼
Python/Quart backend  (localhost:50505/api)
      │
      ├──► Azure AI Search ──► Azure Blob Storage
      │       (retrieve)           (source PDFs)
      │
      └──► Azure OpenAI GPT-4.1-mini
              (generate answer with retrieved context)
```

---

## Want to deploy your own version? (optional, personal Azure account)

If you have your own Azure account and want to deploy the full stack yourself, here's exactly what was done to set this up — you can replicate it.

### 1. Deploy all Azure resources with `azd up`

`azd` (Azure Developer CLI) reads the `azure.yaml` and `infra/` Bicep templates in the repo and provisions everything in one command:

```bash
cd azure-search-openai-demo

azd auth login
azd env new my-rag-demo       # give your environment a name
azd up                        # provisions resources + deploys the app to Azure
```

`azd up` will:
- Create an Azure OpenAI resource with GPT + embedding deployments
- Create an Azure AI Search service (Standard tier)
- Create a Storage account and upload the sample PDFs from `data/`
- Index the documents into AI Search (chunking + embeddings via Document Intelligence)
- Deploy the backend as a Container App and the frontend as a static site
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

You can watch it run with `--verbose` to see exactly what's happening.

### 3. Tear everything down with `azd down`

When you're done experimenting, delete all provisioned resources to stop billing:

```bash
azd down
```

This deletes the resource group and everything inside it. Your local code is untouched.

> `azd down` is the opposite of `azd up` — think of it as "clean up after myself". Always run it when you're done with a demo environment to avoid surprise charges.

### 4. Run locally against your own deployed resources

Once `azd up` has run, you can also run the app locally (same as the student setup) pointing at your own resources:

```bash
azd env get-values   # shows all your resource names and endpoints
cd app/backend
python -m quart --app main:app run --port 50505 --reload
```

No key overrides needed — `azd auth login` handles credentials automatically when running against your own deployment.

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- [Azure CLI (`az`)](https://docs.microsoft.com/cli/azure/install-azure-cli)
- [Azure Developer CLI (`azd`)](https://aka.ms/install-azd)
