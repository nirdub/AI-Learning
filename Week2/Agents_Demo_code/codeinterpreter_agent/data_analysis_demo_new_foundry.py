import os
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import (
    CodeInterpreterTool,
    FilePurpose,
    ListSortOrder,
    MessageRole,
)
from azure.identity import InteractiveBrowserCredential
from dotenv import load_dotenv, find_dotenv

# ── Environment ────────────────────────────────────────────
load_dotenv(find_dotenv())

# NOTE: AgentsClient uses Entra ID auth (scope: https://ai.azure.com/.default).
# Run `az login` before executing this script.
FOUNDRY_PROJECT_ENDPOINT = os.getenv(
    "FOUNDRY_PROJECT_ENDPOINT",
    "https://tdai-foundry.services.ai.azure.com/api/projects/tdai-foundry-project"
)
DEPLOYMENT   = os.getenv("DEPLOYMENT_NAME_GPT_4_mini", "gpt-4o-mini")
STUDENT_NAME = os.getenv("STUDENT_NAME", "student")

CSV_PATH = os.path.join(os.path.dirname(__file__), "asx_100_quaterly_results.csv")
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
    name=f"data-analysis-agent-{STUDENT_NAME}-foundry",
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
'{file_name}' (ASX 100 quarterly results) and do the following:

1. Load the file into a DataFrame. Expected columns:
   name, ASX_Code, sector, industry, revenue, operating_expenses,
   operating_profit, operating_profit_margin, depreciation, interest,
   profit_before_tax, tax, net_profit, EPS, profit_TTM, EPS_TTM.
   Convert any numeric fields stored as strings.

2. Create a bar chart of operating_profit for companies in the
   Financials sector. Label the x-axis with company names.
   Title the chart "Financials sector operating profit - {STUDENT_NAME}".
   Save the chart as a PNG named '{STUDENT_NAME}_financials_operating_profit.png'
   and return that image file to me.

3. Print a table of the top 10 companies by operating_profit.

4. Finish with a short written summary of the key insights.
"""

client.messages.create(
    thread_id=thread.id,
    role="user",
    content=PROMPT
)

# ── 4. Run (blocking — handles all tool calls internally) ──
print("Running analysis...\n" + "-" * 60)
run = client.runs.create_and_process(
    thread_id=thread.id,
    agent_id=agent.id
)
print(f"Run status: {run.status}")
if run.status == "failed":
    print(f"  Run failed: {run.last_error}")
print("-" * 60)

# ── 5. Print the agent's text answer ───────────────────────
# messages.list() defaults to newest-first, so ask for ascending
# order to read the conversation the way it happened.
messages = list(
    client.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING)
)

print()
for msg in messages:
    if msg.role == MessageRole.AGENT:
        for text in msg.text_messages:
            print(text.text.value)
        print()

# ── 6. Collect every file the code interpreter produced ────
# A chart can come back in three different shapes, depending on
# how the model chose to emit it. Handle all three:
#   a) image_contents        — the image is attached to the message
#                              (model called plt.show())
#   b) file_path_annotations — the model called plt.savefig() and
#                              offered the file as a download link
#   c) run step outputs      — the image was emitted during the
#                              code interpreter tool call itself
outputs = []   # list of (file_id, suggested_file_name)

for msg in messages:
    for img in msg.image_contents:
        outputs.append((img.image_file.file_id, None))
    for ann in msg.file_path_annotations:
        # ann.text looks like "sandbox:/mnt/data/chart.png"
        outputs.append((ann.file_path.file_id, os.path.basename(ann.text)))

for step in client.run_steps.list(thread_id=thread.id, run_id=run.id):
    for call in getattr(step.step_details, "tool_calls", None) or []:
        interpreter = getattr(call, "code_interpreter", None)
        for output in getattr(interpreter, "outputs", None) or []:
            if getattr(output, "type", None) == "image":
                outputs.append((output.image.file_id, None))

# Same file can appear in more than one place — keep first occurrence.
unique_outputs = list(dict.fromkeys(outputs))

# ── 7. Download them next to this script ───────────────────
OUT_DIR = os.path.dirname(__file__)

if not unique_outputs:
    print("No image or file output was returned by the code interpreter.")
    print("The model most likely described the chart instead of generating it.")
    print("Try asking explicitly: 'save the chart as a PNG and return the file'.")
else:
    for index, (file_id, suggested_name) in enumerate(unique_outputs, 1):
        extension = os.path.splitext(suggested_name or "")[1] or ".png"
        out_name = f"{STUDENT_NAME}_foundry_chart_{index}{extension}"
        client.files.save(file_id=file_id, file_name=out_name, target_dir=OUT_DIR)
        print(f"[Saved: {os.path.join(OUT_DIR, out_name)}]")

# ── 8. Clean up ────────────────────────────────────────────
# client.files.delete(uploaded_file.id)
# client.delete_agent(agent.id)