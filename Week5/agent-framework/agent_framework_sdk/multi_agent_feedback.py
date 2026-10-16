# Microsoft Agent Framework — Multi-Agent Customer Feedback Pipeline
#
# Same three-agent pipeline as the azure_ai_agents version, but written using
# the higher-level Microsoft Agent Framework SDK:
#
#   agent-framework-core
#   agent-framework-foundry
#   agent-framework-orchestrations
#
# Key difference: SequentialBuilder handles orchestration automatically —
# no manual thread creation, polling, or message retrieval needed.
#
# Prerequisites:
#   pip install agent-framework-core agent-framework-foundry agent-framework-orchestrations python-dotenv azure-identity
#   az login
#
# Reference: https://microsoftlearning.github.io/mslearn-ai-agents/Instructions/Exercises/08-agent-framework-multi-agents.html

import sys
sys.stdout.reconfigure(encoding='utf-8')
import asyncio
import os
from typing import cast
from dotenv import load_dotenv
from azure.identity import AzureCliCredential

from agent_framework import Message #agent-framework sdk
from agent_framework.foundry import FoundryChatClient
from agent_framework.orchestrations import SequentialBuilder #for sequential orchestration, flow of messages from one agent to another

load_dotenv()

FOUNDRY_PROJECT_ENDPOINT = os.getenv("FOUNDRY_PROJECT_ENDPOINT")
DEPLOYMENT = os.getenv("DEPLOYMENT_NAME", "gpt-4o-mini")

# ============================================================
# Agent instructions
# ============================================================

SUMMARIZER_INSTRUCTIONS = """
Summarize the customer's feedback in one short sentence. Keep it neutral and concise.
Example output:
App crashes during photo upload.
User praises dark mode feature.
""".strip()

CLASSIFIER_INSTRUCTIONS = """
Classify the feedback as one of the following: Positive, Negative, or Feature Request.
Respond with exactly one label — nothing else.
""".strip()

ACTION_INSTRUCTIONS = """
Based on the summary and classification, suggest the next action in one short sentence.
Example output:
Escalate as a high-priority bug for the mobile team.
Log as positive feedback to share with design and marketing.
Log as enhancement request for product backlog.
""".strip()

# ============================================================
# Customer feedback to process
# ============================================================

FEEDBACK = """
I use the dashboard every day to monitor metrics, and it works well overall.
But when I'm working late at night, the bright screen is really harsh on my eyes.
If you added a dark mode option, it would make the experience much more comfortable.
"""

# ============================================================
# Main pipeline
# ============================================================

async def main(): #async main function to run the multi-agent pipeline
    print("=" * 60)
    print("MULTI-AGENT CUSTOMER FEEDBACK PIPELINE")
    print("Microsoft Agent Framework SDK")
    print("=" * 60)
    print(f"\nOriginal Feedback:\n{FEEDBACK.strip()}\n")

    # ── Create chat client ───────────────────────────────────
    chat_client = FoundryChatClient( #FoundryChatClient is used to create a chat client that connects to the Foundry project endpoint and uses the specified model deployment.
        credential=AzureCliCredential(),
        project_endpoint=FOUNDRY_PROJECT_ENDPOINT,
        model=DEPLOYMENT,
    )

    # ── Define agents ────────────────────────────────────────
    summarizer_agent = chat_client.as_agent(
        name="summarizer",
        instructions=SUMMARIZER_INSTRUCTIONS,
    )
    classifier_agent = chat_client.as_agent(
        name="classifier",
        instructions=CLASSIFIER_INSTRUCTIONS,
    )
    action_agent = chat_client.as_agent(
        name="action",
        instructions=ACTION_INSTRUCTIONS,
    )

    # ── Build sequential orchestration ───────────────────────
    # output_from="all" collects each agent's response in the final result
    workflow = SequentialBuilder( #workflow builder to orchestrate the agents in sequence, passing the output of one agent as input to the next.
        participants=[summarizer_agent, classifier_agent, action_agent],
        output_from="all",
    ).build()

    # ── Run the pipeline ─────────────────────────────────────
    result = await workflow.run(f"Customer feedback:\n{FEEDBACK}") #run the workflow with the customer feedback as input, and await the result
    outputs = result.get_outputs() #retrieve the outputs from the workflow, which contains the responses from each agent in sequence.

    # ── Display results ──────────────────────────────────────
    agent_names = ["Summarizer", "Classifier", "Action"]
    responses = {} 

    i = 0
    for response in outputs:
        for msg in cast(list[Message], response.messages):
            if msg.role == "assistant":
                label = agent_names[i] if i < len(agent_names) else f"Agent {i+1}"
                print("-" * 60)
                print(f"STEP {i+1} — {label} Agent")
                print("-" * 60)
                print(msg.text)
                print()
                responses[label] = msg.text
                i += 1

    # ── Final summary ────────────────────────────────────────
    print("=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
    for label, text in responses.items():
        print(f"  {label:12s}: {text}")


if __name__ == "__main__":
    asyncio.run(main())
