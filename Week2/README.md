# Week 2 – Azure AI Agents

This week covers building agents using **Azure AI Foundry**. You will run four demos covering function calling and code interpreter, using the `azure-ai-agents` SDK.

> **Note (migration):** All scripts have been migrated from the retired Azure OpenAI Assistants API (`openai.beta.assistants.*`) to the current `azure.ai.agents.AgentsClient` SDK. Authentication now uses `InteractiveBrowserCredential` — a browser window will open when you first run any script. No separate `az login` is required.

| Demo | Script | What it does |
|---|---|---|
| Function Agent | `Function_agent/createAgent.py` | Creates an agent with a custom `fetch_weather` function tool — visible in the Azure AI Foundry portal |
| Function Agent (Classic style) | `Function_agent/createAgent_classic.py` | Same as above but asks the agent its name instead of weather, demonstrating a different query pattern |
| Code Interpreter Agent (streaming) | `codeinterpreter_agent/data_analysis_demo.py` | Uploads a CSV, streams code execution output live, saves generated chart locally. Use Week2/Agents_Demo_code/codeinterpreter_agent/data_analysis_demo_1.py which has updated prompt to use Student name as variable and save the chart (image file) to Foundry |
| Code Interpreter Agent (blocking) | `codeinterpreter_agent/data_analysis_demo_new_foundry.py` | Same analysis using a blocking `create_and_process` run — simpler code, no streaming |

---

## Prerequisites

- Python 3.11 or later
- [VS Code](https://code.visualstudio.com/) with the [Python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python) installed
- Access to the course Azure subscription (your trainer will provide credentials)
- A browser available for the Entra ID login prompt when scripts first run

---

## 1. Open the project in VS Code

1. Open VS Code
2. Click **File → Open Folder**
3. Navigate to and select the `AI-Engineering-TDAI` root folder
4. Click **Select Folder**

---

## 2. Open a terminal in VS Code

1. In the menu bar, click **Terminal → New Terminal**
   - A terminal panel will open at the bottom of the screen

> **Tip:** Use the keyboard shortcut **Ctrl + `** (backtick) to toggle the terminal.

---

## 3. Set up your Python environment

If the course virtual environment is not already activated, run:

```bash
# Windows
.venv\Scripts\activate

# Mac / Linux
source .venv/bin/activate
```

You should see `(.venv)` appear at the start of your terminal prompt.

If the `.venv` folder does not exist yet, create it first:

```bash
python -m venv .venv
```

Then activate it (see above) and install dependencies:

```bash
pip install -r requirements.txt
```

---

## 4. Configure your environment variables

The scripts pick up settings from a `.env` file at the **project root** (`AI-Engineering-TDAI/.env`). The key variables used by Week 2 scripts are:

```
DEPLOYMENT_NAME_GPT_4_mini=gpt-4o-mini
DEPLOYMENT_NAME_GPT_4=gpt-4o
STUDENT_NAME=your-name
FOUNDRY_PROJECT_ENDPOINT=https://<your-foundry-resource>.services.ai.azure.com/api/projects/<your-project-name>
AZURE_TENANT_ID=<provided by trainer>
```

> If `FOUNDRY_PROJECT_ENDPOINT` is not set, the scripts fall back to the course default endpoint automatically.

> If `STUDENT_NAME` is not set, it defaults to `student`. Set it to your own name so your agents and uploaded files are identifiable in the portal.

---

## 5. Authentication

All four scripts use **`InteractiveBrowserCredential`** from the `azure-identity` package. When you run any script for the first time, a browser window will open automatically — sign in with your course Azure account and complete MFA if prompted. After the first login the token is cached for the rest of the session, so subsequent scripts run without opening the browser again.

No `az login` is required. The browser handles everything including multi-factor authentication.

---

## 6. Run the demos

### Demo 1 — Function Agent

Creates an agent with a `fetch_weather` function tool. The agent is visible in the **Azure AI Foundry portal** under **Agents**.

```bash
cd Week2/Agents_Demo_code/Function_agent
python createAgent.py
```

**What to expect:**
- A browser opens for login (first run only)
- Agent is created and visible in the Azure AI Foundry portal under **Agents**
- The agent calls `fetch_weather("Brisbane")` to answer a weather question
- The function result is returned and the agent responds

**Example output:**
```
Created agent: asst_xxxxxxxxxxxx  (visible in Azure AI Foundry portal)
  Name:  weather-agent-student
  Model: gpt-4o-mini

Created thread: thread_xxxxxxxxxxxx
Created message: msg_xxxxxxxxxxxx
Calling function: fetch_weather with args: {'location': 'Brisbane'}
Run status: RunStatus.COMPLETED

===== AGENT OUTPUT =====

I'm sorry, but I couldn't retrieve the weather data for Brisbane at the moment.
Please try again later!
```

> **Why "data not available"?** The `fetch_weather` function in `user_functions.py` uses mock data with a fixed list of cities (New York, London, Tokyo, Melbourne). Brisbane is not in the list, so the function returns "Weather data not available." — the agent correctly reports this back. You can add `"Brisbane": "Sunny, 24°C"` to the mock data to see a successful result.

---

### Demo 2 — Function Agent (Classic style)

Same agent setup but asks "What is your name?" — demonstrates that the agent can respond without calling any function tool.

```bash
cd Week2/Agents_Demo_code/Function_agent
python createAgent_classic.py
```

**What to expect:**
- Agent is created with `gpt-4o` model
- The agent responds to a general question without invoking the weather function
- No function calls are made in this run

**Example output:**
```
Created agent: asst_xxxxxxxxxxxx
  Name:  weather-agent-student-classic
  Model: gpt-4o

Created thread: thread_xxxxxxxxxxxx
Created message: msg_xxxxxxxxxxxx

Run status: RunStatus.COMPLETED

===== AGENT OUTPUT =====

I don't have a personal name, but you can call me Weather Bot!
I'm here to help with weather-related questions.
```

---

### Demo 3 — Code Interpreter Agent (streaming)

Uploads the ASX 100 quarterly results CSV and runs a data analysis with **real-time streaming** of the generated Python code.

```bash
cd Week2/Agents_Demo_code/codeinterpreter_agent
python data_analysis_demo.py
```

> **Note:** Run from the `codeinterpreter_agent/` folder so the CSV file path resolves correctly.

**What to expect:**
- CSV file is uploaded to the Agents service
- Agent is created with the Code Interpreter tool
- Python code written by the agent streams live to your terminal
- Analysis text and top-10 table are printed
- Any generated chart images are saved as `<STUDENT_NAME>_chart_1.png` in the same folder

**Example output:**
```
Uploading 'student_asx_100_quaterly_results.csv' ...
  File ID : assistant-xxxxxxxxxxxx
Created agent: asst_xxxxxxxxxxxx (data-analysis-agent-student)
  Visible in Azure AI Foundry portal > Agents

Running analysis - streaming below:
------------------------------------------------------------
import pandas as pd
df = pd.read_csv('/mnt/data/assistant-xxxxxxxxxxxx')
...
### Key Insights
1. Rio Tinto Limited leads with operating profit of 32,700 million
...
------------------------------------------------------------

[Chart saved: .../student_chart_1.png]
```

---

### Demo 4 — Code Interpreter Agent (blocking)

Same analysis as Demo 3 but uses a **blocking** `create_and_process` run — the terminal waits silently until the full analysis is complete, then prints all output at once.

```bash
cd Week2/Agents_Demo_code/codeinterpreter_agent
python data_analysis_demo_new_foundry.py
```

**What to expect:**
- Same CSV upload and agent creation as Demo 3
- Terminal shows "Running analysis..." and waits
- Full analysis and insights printed after run completes
- Chart saved as `<STUDENT_NAME>_foundry_chart_1.png`

**Example output:**
```
Uploading 'student_asx_100_quaterly_results.csv' ...
  File ID : assistant-xxxxxxxxxxxx
Created agent: asst_xxxxxxxxxxxx (data-analysis-agent-student-foundry)
  Visible in Azure AI Foundry portal > Agents

Running analysis...
------------------------------------------------------------
Run status: RunStatus.COMPLETED
------------------------------------------------------------

### Key Insights from the ASX 100 Quarterly Results
1. Rio Tinto Limited leads with an operating profit of 32,700 million ...
...

[Chart saved: .../student_foundry_chart_1.png]
```

**Key differences between Demo 3 and Demo 4:**

| | Demo 3 — Streaming (`data_analysis_demo.py`) | Demo 4 — Blocking (`data_analysis_demo_new_foundry.py`) |
|---|---|---|
| Output style | Streams code and text live as it's written | Waits silently, prints everything at the end |
| Run method | `client.runs.stream()` + `AgentEventHandler` | `client.runs.create_and_process()` |
| Agent name suffix | `data-analysis-agent-<name>` | `data-analysis-agent-<name>-foundry` |
| Chart filename | `<name>_chart_1.png` | `<name>_foundry_chart_1.png` |
| Auth | `InteractiveBrowserCredential` | `InteractiveBrowserCredential` |
| SDK | `azure-ai-agents` | `azure-ai-agents` |

---

## How the function calling loop works

Both function agent scripts use **manual polling** to handle tool calls. Here is the flow:

```
create run
    │
    ▼
while status in [QUEUED, IN_PROGRESS, REQUIRES_ACTION]:
    │
    ├─ REQUIRES_ACTION ──► extract tool calls
    │                       call Python function locally
    │                       submit results back to agent
    │
    └─ QUEUED / IN_PROGRESS ──► sleep 1s, poll again
    │
    ▼
COMPLETED → print messages
```

This pattern is the standard approach for custom function tools with `AgentsClient`. The agent decides when to call a function; your code executes it locally and returns the result.

---

## Troubleshooting

**`ModuleNotFoundError`**
You are not in the virtual environment, or dependencies are not installed:
```bash
.venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

**`FileNotFoundError: CSV file not found`**
Run `data_analysis_demo.py` from the `codeinterpreter_agent/` folder, not from the project root:
```bash
cd Week2/Agents_Demo_code/codeinterpreter_agent
python data_analysis_demo.py
```

**Browser login keeps opening / token not cached**
The browser login caches a token for the session. If you are running scripts in separate terminal sessions, the browser may open again for each new session. This is normal behaviour with `InteractiveBrowserCredential`.

**`ClientAuthenticationError` — MFA required**
The `InteractiveBrowserCredential` browser window supports MFA. Complete the MFA prompt in the browser before the window closes. If the window closes before you finish, re-run the script.

**`Run failed: Rate limit is exceeded`**
The Azure resource has hit its token quota. Wait a minute and try again, or ask your trainer to check the deployment quota in Azure AI Foundry.

**`RunStatus.FAILED` with no error detail**
Check that the `FOUNDRY_PROJECT_ENDPOINT` in your `.env` file (or the default hardcoded value) matches your Azure AI Foundry project URL. Ask your trainer for the correct endpoint.

**Weather bot says "data not available" for your city**
The `fetch_weather` function in `user_functions.py` uses mock data. Add your city to the `mock_weather_data` dictionary in that file.
