# Week 4 - Run the RAG Chatbot Demo

This guide helps to run **"Chat with your data"** app on your machine. The app answers questions about sample company documents (Northwind Health plans, employee handbook) using **Azure AI Search** + **Azure OpenAI**.

The Azure resources are already set up by your trainer. You only run the app locally.

>Written for **Windows + VS Code**. Mac/Linux notes are at the end.

---

## Contents

1. [Install the prerequisites](#1-install-the-prerequisites)
2. [Get the code](#2-get-the-code)
3. [Open the project in VS Code](#3-open-the-project-in-vs-code)
4. [Create and activate a Python virtual environment](#4-create-and-activate-a-python-virtual-environment)
5. [Run the setup script](#5-run-the-setup-script)
6. [Start the app](#6-start-the-app)
7. [Open the app and try it](#7-open-the-app-and-try-it)
8. [Stopping and restarting later](#8-stopping-and-restarting-later)
9. [Troubleshooting](#9-troubleshooting)
10. [Mac / Linux](#10-mac--linux)

---

## 1. Install the prerequisites

Install each of these, then **close and reopen VS Code** so it picks them up.

| Tool | Version | Download |
|---|---|---|
| Git | any | https://git-scm.com/downloads |
| Python | **3.11 or newer** | https://www.python.org/downloads/ (tick **"Add python.exe to PATH"** during install) |
| Node.js | **20 or newer** (LTS) | https://nodejs.org/ |
| Azure CLI (`az`) | latest | https://aka.ms/installazurecliwindows |
| Azure Developer CLI (`azd`) | latest | https://aka.ms/install-azd |
| VS Code | latest | https://code.visualstudio.com/ |

**Check everything is installed.** Open a terminal in VS Code (`` Ctrl+` ``) and run:

```powershell
git --version
python --version     # must show 3.11 or higher
node --version       # must show v20 or higher
az --version
azd version
```

If any command says *"not recognized"*, that tool isn't installed or isn't on your PATH. Reinstall it, then restart VS Code.

Also install the **Python** extension in VS Code (`Ctrl+Shift+X` → search **Python** → the one by Microsoft).

---

## 2. Get the code

**First time:** clone the repository.

```powershell
git clone https://github.com/TDAI-admin/AI-Engineering-TDAI.git
```

**Already cloned it before?** Get the latest version. It includes bug fixes:

```powershell
cd AI-Engineering-TDAI
git pull
```

---

## 3. Open the project in VS Code

In VS Code: **File → Open Folder…** → select the **`AI-Engineering-TDAI\azure-search-openai-demo`** folder.

> Open the `azure-search-openai-demo` folder itself, not the parent repo folder. Every command below assumes your terminal starts in `azure-search-openai-demo`.

Open a terminal (`` Ctrl+` ``) and confirm where you are:

```powershell
pwd        # should end in ...\AI-Engineering-TDAI\azure-search-openai-demo
```

---

## 4. Create and activate a Python virtual environment

A virtual environment (`.venv`) keeps this app's Python packages separate from everything else on your laptop.

> **Do this before running the setup script.** The script installs Python packages into whichever Python is active. If the venv isn't active, the packages go into your system Python, and the app can fail later with confusing errors.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Your prompt should now start with **`(.venv)`**:

```
(.venv) PS C:\...\azure-search-openai-demo>
```

> **Error: "running scripts is disabled on this system"?** Run this once, then try `.venv\Scripts\Activate.ps1` again:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
> ```

**Tell VS Code to use this venv:** `Ctrl+Shift+P` → **Python: Select Interpreter** → choose the one showing **`.venv`**. After this, new VS Code terminals activate the venv automatically.

---

## 5. Run the setup script

In the **same terminal** (with `(.venv)` showing), run:

```powershell
powershell -ExecutionPolicy Bypass -File .\student-setup.ps1
```

The script runs 6 steps:

| Step | What it does | What you'll see |
|---|---|---|
| 1/6 | Checks `az`, `azd`, `python`, `node` are installed | `All prerequisites found.` |
| 2/6 | Writes the app's config file (`.azure\tdai-rag-chatbot\.env`) with the shared Azure resource names | `.env written to ...` |
| 3/6 | Registers the `tdai-rag-chatbot` azd environment | `azd environment set to 'tdai-rag-chatbot'.` |
| 4/6 | Signs you in to Azure | **A browser window opens. Sign in with your course account.** |
| 5/6 | Installs and builds the web frontend (`npm install` + `npm run build`) | Takes 1–5 minutes. Warnings about *"chunks larger than 500 kB"* are normal. |
| 6/6 | Installs the Python packages into your venv | Takes 1–3 minutes |

It finishes with:

```
=== Setup complete! ===
```

If it stops with a red `ERROR`, see [Troubleshooting](#9-troubleshooting).

> You only need to run the setup script **once**. Run it again only if you `git pull` new changes or something breaks.

---

## 6. Start the app

Trainer will give you **two keys**: an **OpenAI key** and a **Search key**.

> Keep the keys private. Don't paste them into files, commit them to Git, or share them in chat. You'll type them into the terminal each time you start the app.

In the VS Code terminal (with `(.venv)` showing), from the `azure-search-openai-demo` folder:

```powershell
cd app\backend
$env:AZURE_OPENAI_API_KEY_OVERRIDE="<OpenAI key from trainer>"
$env:AZURE_SEARCH_KEY_OVERRIDE="<Search key from trainer>"
python -m quart --app main:app run --port 50505 --reload
```

Wait until you see this line:

```
Running on http://127.0.0.1:50505 (CTRL + C to quit)
```

**Leave this terminal running.** The app runs only while it's open.

---

## 7. Open the app and try it

**Option A: inside VS Code (Simple Browser)**
`Ctrl+Shift+P` → **Simple Browser: Show** → enter `http://localhost:50505`
(or open the **Ports** tab in the bottom panel and click the globe icon next to port `50505`).

**Option B: your normal browser**
Go to **http://localhost:50505**

You should see **"Chat with your data"** with example questions.

**Try it:**

1. Click an example question, or type: *What is included in my Northwind Health Plus plan?*
2. Wait a few seconds. The answer streams in with **citations** (numbered links to the source PDFs).
3. Click the 💡 **lightbulb** icon under an answer to see the **thought process**: the search query the AI generated and the prompt it used.
4. Click the 📋 **clipboard** icon to see the **supporting content**: the exact document chunks that AI Search retrieved.
5. Open **Developer settings** (top right) to change the retrieval mode (text / vectors / hybrid), the number of results, and more. Then ask the same question again and compare the answers.

If you get an answer with citations, your setup is complete.

---

## 8. Stopping and restarting later

**To stop the app:** click in the terminal where it's running and press **`Ctrl+C`**.

**To start it again later** (no need to rerun the setup script):

```powershell
# from the azure-search-openai-demo folder
.venv\Scripts\Activate.ps1                     # skip if (.venv) already shows
cd app\backend
$env:AZURE_OPENAI_API_KEY_OVERRIDE="<OpenAI key from trainer>"
$env:AZURE_SEARCH_KEY_OVERRIDE="<Search key from trainer>"
python -m quart --app main:app run --port 50505 --reload
```

> The two `$env:` keys last only for **that terminal window**. In a new terminal, you have to set them again.

> Run **only one copy** of the app at a time. If you start it in several terminals, your browser may talk to an old copy. Stop old ones with `Ctrl+C` first.

---

## 9. Troubleshooting

### The page shows "Unexpected Application Error! f is not a function"

Your copy has an older frontend with a bug that crashes the app in newer versions of Edge, Chrome and VS Code's Simple Browser. To fix it:

```powershell
# from the azure-search-openai-demo folder, stop the app first (Ctrl+C)
git pull
cd app\frontend
npm run build
cd ..\backend
# then start the app again (step 6)
```

Then reload the page using a fresh address, such as **http://localhost:50505/?v=2**. Browsers keep the old page for a while, and the new address skips that copy.

### The app looks like an old version, or a fix doesn't show up

Your browser is showing a saved (cached) copy. Open **http://localhost:50505/?v=2**, or any other number, or press **`Ctrl+F5`** in Edge or Chrome.

> `localhost:50505` and `127.0.0.1:50505` are the same app, but the browser keeps a **separate** saved copy for each address. The VS Code **Ports** tab opens `127.0.0.1`, so a fix can show up on one address but not the other. Use a fresh `?v=` number on whichever address you open.
>
> To clear VS Code's Simple Browser cache completely: `Ctrl+Shift+P` → **Developer: Open Webview Developer Tools** → right-click the reload button → **Empty Cache and Hard Reload**.

### `No module named quart` (or another `No module named ...`)

The venv isn't active, or the packages were installed into a different Python.

```powershell
# from the azure-search-openai-demo folder
.venv\Scripts\Activate.ps1
pip install -r app\backend\requirements.txt
```

### `running scripts is disabled on this system`

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### `Exception: Error loading azd env` or `No default azd env file found`

Either `azd` isn't installed or the app can't find its environment. Check the following:

```powershell
azd version                        # is azd installed?
# from the azure-search-openai-demo folder:
azd env list                       # should show tdai-rag-chatbot with IsDefault = true
azd env select tdai-rag-chatbot    # sets it as the default
```

If `tdai-rag-chatbot` isn't listed, run the setup script again (step 5).

### Setup script fails with `The string is missing the terminator`, `unexpected character "»"`, or `Update available`

You have an older copy of `student-setup.ps1` that doesn't work in Windows PowerShell 5.1. Get the fixed version and run it again:

```powershell
# from the azure-search-openai-demo folder
git pull
powershell -ExecutionPolicy Bypass -File .\student-setup.ps1
```

The script rewrites `.azure\tdai-rag-chatbot\.env` each time, so the broken file gets replaced.

### `Forbidden`, `401 Unauthorized`, `Access denied`, or `invalid subscription key` when asking a question

The terminal logs `Operation returned an invalid status 'Forbidden'`, and the page shows *"The app encountered an error processing your request"*.

The keys aren't set in the terminal that's running the app, or there's a typo. Stop the app (`Ctrl+C`), then check:

```powershell
$env:AZURE_OPENAI_API_KEY_OVERRIDE   # should print the OpenAI key
$env:AZURE_SEARCH_KEY_OVERRIDE       # should print the Search key
```

If either prints nothing, set it again (step 6) and restart the app. Make sure you copy each key exactly, with no extra spaces or missing characters. If the keys still don't work, ask your trainer. The keys may have been changed.

### `AzureCliCredential` / `DefaultAzureCredential` / "Please run 'az login'" errors

Your Azure sign-in has expired or used the wrong account:

```powershell
az login          # sign in with your COURSE account
```

Then restart the app.

### Answers work, but clicking a citation doesn't show the PDF

The PDF preview loads from Azure Storage using your own Azure sign-in, not the keys. Run `az login` with your course account and restart the app. If it still fails, tell your trainer. Your account may need access to the storage account.

### Port 50505 is already in use / the app behaves strangely

An old copy of the app is probably still running. Find and stop it:

```powershell
Get-NetTCPConnection -LocalPort 50505 -State Listen | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

If it says *"No MSFT_NetTCPConnection objects found"*, nothing is using the port, so there's nothing to stop.

Then start the app again (step 6).

### `npm install` or `npm run build` fails

- Check `node --version` shows **v20 or newer**. Upgrade Node.js if not.
- Delete the installed packages and try again:
  ```powershell
  cd app\frontend
  Remove-Item -Recurse -Force node_modules
  npm install
  npm run build
  ```

### `python` opens the Microsoft Store, or shows the wrong version

Windows has a placeholder `python` command. Reinstall Python from python.org and tick **"Add python.exe to PATH"**, or create the venv with the Python launcher:

```powershell
py -3.11 -m venv .venv
```

### Still stuck?

Send your trainer:
1. The **exact error text** (copy the terminal output, or take a screenshot)
2. Which step you were on
3. The output of `python --version`, `node --version` and `azd version`

**Never include the keys in screenshots or messages.**

---

## 10. Mac / Linux

The steps are the same. Only the commands differ:

| Windows (PowerShell) | Mac / Linux (bash/zsh) |
|---|---|
| `python -m venv .venv` | `python3 -m venv .venv` |
| `.venv\Scripts\Activate.ps1` | `source .venv/bin/activate` |
| `powershell -ExecutionPolicy Bypass -File .\student-setup.ps1` | `bash student-setup.sh` |
| `cd app\backend` | `cd app/backend` |
| `$env:AZURE_OPENAI_API_KEY_OVERRIDE="..."` | `export AZURE_OPENAI_API_KEY_OVERRIDE="..."` |
| `$env:AZURE_SEARCH_KEY_OVERRIDE="..."` | `export AZURE_SEARCH_KEY_OVERRIDE="..."` |
| `python -m quart --app main:app run --port 50505 --reload` | same, or use `python3` if `python` isn't found |

---

## How it works (quick picture)

```
Your browser  ──►  http://localhost:50505
                        │
                        ▼
          Python/Quart backend (running on your laptop)
                        │
      ┌─────────────────┼──────────────────────┐
      ▼                 ▼                      ▼
Azure AI Search    Azure OpenAI           Azure Blob Storage
(finds relevant    (writes the answer     (the source PDFs,
 document chunks)   from those chunks)     for citations)
```

1. You ask a question.
2. The backend asks **Azure OpenAI** to turn your question into a good search query.
3. **Azure AI Search** finds the most relevant chunks of the documents, using keyword and vector search.
4. The backend sends your question and those chunks to **Azure OpenAI**, which writes an answer that cites its sources.

This pattern is called **RAG: Retrieval Augmented Generation**.
