# Week 5 — Azure AI Content Safety, Semantic Kernel & Agent Framework

This week covers three areas:

1. **Session 2** — Azure AI Content Safety, Computer Vision, and Language services
2. **Semantic Kernel** — Getting started with Microsoft's AI orchestration framework
3. **Agent Framework** — Multi-agent orchestration with the Azure AI Agents SDK

---

## Prerequisites

All scripts use the shared virtual environment at the repo root. Activate it before running anything:

```bash
# From the repo root
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Mac/Linux
```

Install dependencies if needed:

```bash
pip install azure-ai-contentsafety azure-ai-vision-imageanalysis azure-ai-textanalytics python-dotenv
pip install semantic-kernel
pip install azure-ai-agents azure-identity
pip install agent-framework-core agent-framework-foundry agent-framework-orchestrations
```

---

## Session 2 — Azure AI Content Safety

Located in `Week5/session2/`.

### Setup

Copy the `.env` file template and fill in your Azure credentials:

```
AZURE_CONTENT_SAFETY_ENDPOINT=https://<your-resource>.cognitiveservices.azure.com/
AZURE_CONTENT_SAFETY_KEY=<your-key>
AZURE_COMPUTER_VISION_ENDPOINT=https://<your-resource>.cognitiveservices.azure.com/
AZURE_COMPUTER_VISION_KEY=<your-key>
AZURE_LANGUAGE_ENDPOINT=https://<your-resource>.cognitiveservices.azure.com/
AZURE_LANGUAGE_KEY=<your-key>
```

> If you are using a single Azure AI Services multi-service resource, all endpoints and keys will be the same value.

---

### Scripts

#### 1. Text Content Safety — `TextAnalysisContentSafety.py`

Analyses a short text string for harmful content across four categories: **Hate, Self-Harm, Sexual, Violence**. Returns a severity score (0 = safe, 6 = high) for each.

```bash
cd Week5/session2
python TextAnalysisContentSafety.py
```

---

#### 2. Text Content Safety with Full Report — `TextAnalysisContentSafetyProfanity.py`

Reads `sample.txt` and runs a full content safety analysis with a detailed breakdown per category and an overall assessment.

```bash
cd Week5/session2
python TextAnalysisContentSafetyProfanity.py
```

---

#### 3. Content Safety + PII Detection — `TextAnalysisContentSafetyPII.py`

Reads `sample.txt` and runs two analyses:

- **Content Safety** — detects harmful categories
- **PII Detection** — identifies personally identifiable information (names, emails, phone numbers, addresses, bank details, IP addresses, etc.) using Azure AI Language, and returns a redacted version of the text

```bash
cd Week5/session2
python TextAnalysisContentSafetyPII.py
```

---

#### 4. Image Analysis — `ImageAnalysis.py`

Loops through a list of image URLs and runs three analyses on each:

- **Harmful content detection** (Content Safety) — checks for adult, violent, or hate content
- **OCR / text extraction** (Computer Vision) — reads any text visible in the image
- **Person detection** (Computer Vision) — identifies and counts people with bounding boxes and confidence scores

```bash
cd Week5/session2
python ImageAnalysis.py
```

---

#### 5. Blocklist Management — `BlockList.py`

An interactive demo that walks through the full lifecycle of a custom content blocklist:

1. Create a blocklist
2. Add custom blocked terms (supports wildcard patterns, e.g. `k*ll`)
3. Wait for propagation
4. Test text samples against the blocklist
5. List, inspect, and remove items
6. Delete the blocklist (optional)

```bash
cd Week5/session2
python BlockList.py
```

The script will prompt you to press Enter to start and ask whether to delete the blocklist at the end. Blocklist changes take approximately 5 minutes to propagate in production — the demo uses a 10-second wait for illustration purposes.

---

## Semantic Kernel — Getting Started

Located in `Week5/semantic-kernal/`.

Semantic Kernel is Microsoft's open-source SDK for building AI-powered applications. It lets you define **plugins** (collections of functions) and invoke them through a **kernel** that manages AI service connections.

### Setup

Create a `.env` file in `Week5/semantic-kernal/` (copy from `.env.example`) with the following:

```
GLOBAL_LLM_SERVICE="AzureOpenAI"
AZURE_OPENAI_ENDPOINT="https://<your-resource>.cognitiveservices.azure.com/"
AZURE_OPENAI_API_KEY="<your-api-key>"
AZURE_OPENAI_CHAT_DEPLOYMENT_NAME="<your-deployment-name>"
AZURE_OPENAI_TEXT_DEPLOYMENT_NAME="<your-deployment-name>"
AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME="<your-embedding-deployment-name>"
AZURE_OPENAI_API_VERSION="2024-12-01-preview"
```

### Running the Notebook

Open and run `00-getting-started.ipynb` in VS Code or Jupyter. The notebook:

1. Initialises a `Kernel` instance
2. Connects it to Azure OpenAI using your API key
3. Loads the `FunPlugin` — a collection of prompt-based functions defined in `FunPlugin/`
4. Invokes the `Joke` function with a topic and style to generate a joke

### FunPlugin Structure

Each function inside a plugin is a folder containing two files:

| File | Purpose |
|---|---|
| `skprompt.txt` | The prompt template sent to the model |
| `config.json` | Settings such as max tokens and temperature |

Available functions: `Joke`, `Excuses`, `Limerick`

To invoke a different function, change `plugin["Joke"]` in the notebook to `plugin["Excuses"]` or `plugin["Limerick"]`.

---

## Agent Framework — Multi-Agent Orchestration

Located in `Week5/agent-framework/`.

Both examples implement the same three-agent customer feedback pipeline, but using two different SDKs. This lets you see how the same problem is solved at different levels of abstraction.

```
Customer Feedback
      │
      ▼
┌─────────────┐
│  Summarizer │  → one neutral sentence capturing the core point
└─────────────┘
      │
      ▼
┌─────────────┐
│  Classifier │  → Positive / Negative / Feature Request
└─────────────┘
      │
      ▼
┌─────────────┐
│   Action    │  → recommended follow-up step
└─────────────┘
```

---

### SDK Comparison

| | `azure.ai.agents` | `agent_framework` |
|---|---|---|
| **Package** | `azure-ai-agents` | `agent-framework-core` + `agent-framework-foundry` + `agent-framework-orchestrations` |
| **Level** | Low-level REST SDK | High-level orchestration framework |
| **Orchestration** | Manual — you chain agents by passing outputs between threads yourself | Built-in `SequentialBuilder` (also: `ConcurrentBuilder`, `HandoffBuilder`, `GroupChatBuilder`) |
| **Async** | Synchronous | Async (`asyncio`) |
| **Thread management** | Manual — create thread, poll run status, retrieve messages | Automatic — handled internally |
| **Agent lifecycle** | Agents are persistent Foundry resources (must delete manually) | Agents are lightweight in-process objects, no cleanup needed |
| **Auth** | `InteractiveBrowserCredential` or API key | `AzureCliCredential` (`az login`) |
| **When to use** | Full control, production workloads, tool calling, file search | Rapid prototyping, multi-agent patterns, learning the orchestration concepts |

---

### Setup (both examples)

Requires Azure login:

```bash
az login
```

Install dependencies:

```bash
pip install azure-ai-agents azure-identity python-dotenv
pip install agent-framework-core agent-framework-foundry agent-framework-orchestrations
```

---

### Example 1 — `azure_ai_agents/multi_agent_feedback.py`

Uses `azure.ai.agents.AgentsClient`. Agents are created as persistent Foundry resources. Each step manually creates a thread, processes a run, retrieves messages, and passes the text output to the next agent. Agents are deleted in a `finally` block at the end.

```bash
cd Week5/agent-framework/azure_ai_agents
python multi_agent_feedback.py
```

`.env` variables:

```
FOUNDRY_PROJECT_ENDPOINT=https://<your-resource>.services.ai.azure.com/api/projects/<your-project>
DEPLOYMENT_NAME=gpt-4o-mini
AZURE_TENANT_ID=<your-tenant-id>
```

---

### Example 2 — `agent_framework_sdk/multi_agent_feedback.py`

Uses the Microsoft Agent Framework SDK. Agents are defined with `FoundryChatClient.as_agent()` and wired together with `SequentialBuilder`. A single `await workflow.run(feedback)` call drives the entire pipeline — no thread management or polling required.

```bash
cd Week5/agent-framework/agent_framework_sdk
python multi_agent_feedback.py
```

`.env` variables:

```
FOUNDRY_PROJECT_ENDPOINT=https://<your-resource>.services.ai.azure.com/api/projects/<your-project>
DEPLOYMENT_NAME=gpt-4o-mini
```

