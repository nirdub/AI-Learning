import os
import warnings
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import (
    AgentEventHandler, CodeInterpreterTool, FilePurpose, MessageRole,
    MessageDeltaChunk, RunStepDeltaChunk,
)
from azure.identity import InteractiveBrowserCredential
from dotenv import load_dotenv, find_dotenv

warnings.filterwarnings("ignore", category=DeprecationWarning)

# ── Environment ────────────────────────────────────────────
load_dotenv(find_dotenv())

# NOTE: Migrated from the retired Azure OpenAI Assistants API (beta.assistants.*)
# to the Azure AI Agents SDK (azure.ai.agents.AgentsClient).
# AgentsClient uses Entra ID auth (scope: https://ai.azure.com/.default).
# Run `az login` before executing this script.
FOUNDRY_PROJECT_ENDPOINT = os.getenv(
    "FOUNDRY_PROJECT_ENDPOINT",
    "https://tdai-foundry.services.ai.azure.com/api/projects/tdai-foundry-project"
)
DEPLOYMENT   = os.getenv("DEPLOYMENT_NAME_GPT_4_mini", "gpt-4o-mini")
STUDENT_NAME = os.getenv("STUDENT_NAME", "student")

CSV_PATH = os.path.join(os.path.dirname(__file__), "nifty_500_quarterly_results.csv")
if not os.path.exists(CSV_PATH):
    raise FileNotFoundError(f"CSV not found: {CSV_PATH}")

# ── Client (Entra auth — opens browser for MFA login) ──────
TENANT_ID = os.getenv("AZURE_TENANT_ID", "3591ff50-2b90-4b13-b7e0-246e055ac456")
client = AgentsClient(
    endpoint=FOUNDRY_PROJECT_ENDPOINT,
    credential=InteractiveBrowserCredential(tenant_id=TENANT_ID),
)

# ── 1. Upload CSV ──────────────────────────────────────────
file_name = f"{STUDENT_NAME}_{os.path.basename(CSV_PATH)}"
print(f"Uploading '{file_name}' ...")
with open(CSV_PATH, "rb") as f:
    uploaded_file = client.files.upload_and_poll(
        file=(file_name, f),
        purpose=FilePurpose.AGENTS
    )
print(f"  File ID : {uploaded_file.id}")


# ── 2. Create agent with code interpreter ──────────────────
code_interpreter = CodeInterpreterTool(file_ids=[uploaded_file.id])

agent = client.create_agent(
    model=DEPLOYMENT,
    name=f"data-analysis-agent-{STUDENT_NAME}",
    instructions="You are a helpful agent that analyzes financial data from a CSV file and generates insights, charts, and tables based on user requests.",
    tools=code_interpreter.definitions,
    tool_resources=code_interpreter.resources,
)
print(f"Created agent: {agent.id} ({agent.name})")
print("  Visible in Azure AI Foundry portal > Agents\n")

# ── 3. Create thread and message ───────────────────────────
thread = client.threads.create()

PROMPT = f"""
You are a data-analysis agent. Analyze the uploaded CSV file
(ASX 100 quarterly results) and do the following:

1. Load the file into a DataFrame. Expected columns:
   name, ASX_Code, sector, industry, revenue, operating_expenses,
   operating_profit, operating_profit_margin, depreciation, interest,
   profit_before_tax, tax, net_profit, EPS, profit_TTM, EPS_TTM.
   Convert any numeric fields stored as strings.

2. Create a bar chart of operating_profit for companies in the
   Financials sector. Label the x-axis with company names.
   
   Save the chart as:
   /mnt/data/{STUDENT_NAME}_nifty_analysis.png

   Attach this PNG image file to your final response.

3. Print a table of the top 10 companies by operating_profit.

4. Finish with a short written summary of the key insights.
"""

client.messages.create(
    thread_id=thread.id,
    role="user",
    content=PROMPT
)

# ── 4. Stream the run ──────────────────────────────────────
# Shows code being written and text output in real time.
class EventHandler(AgentEventHandler):
    def on_message_delta(self, delta: MessageDeltaChunk) -> None:
        if delta.text:
            print(delta.text, end="", flush=True)

    def on_run_step_delta(self, delta: RunStepDeltaChunk) -> None:
        details = delta.delta.step_details if delta.delta else None
        if details and hasattr(details, "tool_calls") and details.tool_calls:
            for tc in details.tool_calls:
                if tc.type == "code_interpreter" and tc.code_interpreter:
                    if tc.code_interpreter.input:
                        print(tc.code_interpreter.input, end="", flush=True)

print("Running analysis — streaming below:\n" + "-" * 60)

with client.runs.stream(
    thread_id=thread.id,
    agent_id=agent.id,
    event_handler=EventHandler(),
) as stream:
    stream.until_done()

print("\n" + "-" * 60)

# ── 5. Download any generated charts ──────────────────────
messages = client.messages.list(thread_id=thread.id)
chart_index = 1
for msg in messages:
    if msg.role == MessageRole.AGENT:
        for item in msg.content:
            if item.type == "image_file":
                file_id = item.image_file.file_id
                img_bytes = b"".join(client.files.get_content(file_id))
                out_path = os.path.join(
                    os.path.dirname(__file__),
                    f"{STUDENT_NAME}_chart_{chart_index}.png"
                )
                with open(out_path, "wb") as f:
                    f.write(img_bytes)
                print(f"\n[Chart saved: {out_path}]")
                chart_index += 1

# ── 6. Clean up uploaded file ──────────────────────────────
# client.files.delete(uploaded_file.id)
# client.delete_agent(agent.id)