import os
import json
import time
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import RunStatus, MessageRole, ToolOutput
from azure.identity import InteractiveBrowserCredential
from dotenv import load_dotenv, find_dotenv
from user_functions import (
    weather_tool_definition,
    fetch_weather
)

# -------------------------------------------------------
# Environment
# -------------------------------------------------------
load_dotenv(find_dotenv())

# NOTE: Originally used the classic openai.azure.com endpoint with
# AzureOpenAI(azure_ad_token_provider=...) and the retired
# beta.assistants API. Migrated to azure.ai.agents.AgentsClient
# which still uses Entra ID auth (DefaultAzureCredential).
# Run `az login` before executing this script.
FOUNDRY_PROJECT_ENDPOINT = os.getenv(
    "FOUNDRY_PROJECT_ENDPOINT",
    "https://tdai-foundry.services.ai.azure.com/api/projects/tdai-foundry-project"
)
DEPLOYMENT = os.getenv("DEPLOYMENT_NAME_GPT_4", "gpt-4o")
STUDENT_NAME = os.getenv("STUDENT_NAME", "student")

# -------------------------------------------------------
# Client — Entra auth via browser (supports MFA)
# -------------------------------------------------------
TENANT_ID = os.getenv("AZURE_TENANT_ID", "3591ff50-2b90-4b13-b7e0-246e055ac456")
client = AgentsClient(
    endpoint=FOUNDRY_PROJECT_ENDPOINT,
    credential=InteractiveBrowserCredential(tenant_id=TENANT_ID),
)

# -------------------------------------------------------
# Create agent
# -------------------------------------------------------
agent = client.create_agent(
    model=DEPLOYMENT,
    name=f"weather-agent-{STUDENT_NAME}-classic",
    instructions="You are a weather bot. Use fetch_weather to answer weather questions.",
    tools=[{"type": "function", "function": weather_tool_definition}],
)
print(f"Created agent: {agent.id}")
print(f"  Name:  {agent.name}")
print(f"  Model: {agent.model}")
print()

# -------------------------------------------------------
# Function registry
# -------------------------------------------------------
function_registry = {
    "fetch_weather": fetch_weather
}

# -------------------------------------------------------
# Create thread and send user message
# -------------------------------------------------------
thread = client.threads.create()
print(f"Created thread: {thread.id}")

msg = client.messages.create(
    thread_id=thread.id,
    role="user",
    content="Hello, what is weather in Melbourne?"
)
print(f"Created message: {msg.id}")
print()

# -------------------------------------------------------
# Run agent with manual function call handling
# -------------------------------------------------------
run = client.runs.create(
    thread_id=thread.id,
    agent_id=agent.id,
)

max_iterations = 30
iteration = 0

while run.status in [RunStatus.QUEUED, RunStatus.IN_PROGRESS, RunStatus.REQUIRES_ACTION] and iteration < max_iterations:
    iteration += 1

    if run.status == RunStatus.REQUIRES_ACTION:
        tool_calls = run.required_action.submit_tool_outputs.tool_calls
        tool_outputs = []

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            print(f"Calling function: {function_name} with args: {function_args}")

            if function_name in function_registry:
                function_result = function_registry[function_name](**function_args)
                tool_outputs.append(
                    ToolOutput(tool_call_id=tool_call.id, output=function_result)
                )

        run = client.runs.submit_tool_outputs(
            thread_id=thread.id,
            run_id=run.id,
            tool_outputs=tool_outputs,
        )
    else:
        time.sleep(1)
        run = client.runs.get(
            thread_id=thread.id,
            run_id=run.id,
        )

print(f"Run status: {run.status}")

# -------------------------------------------------------
# Display output
# -------------------------------------------------------
messages = client.messages.list(thread_id=thread.id)
print("\n===== AGENT OUTPUT =====\n")
for m in messages:
    if m.role == MessageRole.AGENT:
        for c in m.content:
            if c.type == "text":
                print(c.text.value)

# -------------------------------------------------------
# Cleanup — uncomment to delete after testing
# -------------------------------------------------------
# client.delete_agent(agent.id)
# print("Deleted agent.")
