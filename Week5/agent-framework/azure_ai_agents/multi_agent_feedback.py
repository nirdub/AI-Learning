# Azure AI Agent Framework — Multi-Agent Customer Feedback Pipeline
#
# Demonstrates sequential agent orchestration using the Azure AI Agents SDK.
# Three specialised agents process a piece of customer feedback in order:
#
#   1. Summarizer  — condenses the feedback into one neutral sentence
#   2. Classifier  — labels it as Positive / Negative / Feature Request
#   3. Action      — recommends a concrete follow-up action
#
# Each agent's output becomes the next agent's input, forming a pipeline.
#
# Prerequisites:
#   pip install azure-ai-agents azure-identity python-dotenv
#   az login   (Entra ID browser auth is used — no API key needed)
#
# Reference: https://microsoftlearning.github.io/mslearn-ai-agents/

import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
from azure.ai.agents import AgentsClient #agents client to connect to foudry project via azure.ai.agents sdk    
from azure.ai.agents.models import (
    AgentThreadCreationOptions, #similar to email thread, it is a collection of messages between user and agent
    ThreadMessageOptions, 
    MessageRole, #we have to define if message role is user input or agent output
    RunStatus, #thread run status, to check if the thread is completed or not like a logger to check if the thread is completed or not
)
from azure.identity import InteractiveBrowserCredential

load_dotenv()

FOUNDRY_PROJECT_ENDPOINT = os.getenv("FOUNDRY_PROJECT_ENDPOINT")
DEPLOYMENT = os.getenv("DEPLOYMENT_NAME", "gpt-4o-mini")
TENANT_ID = os.getenv("AZURE_TENANT_ID", "3591ff50-2b90-4b13-b7e0-246e055ac456")

# ============================================================
# Agent instructions
# ============================================================
#customer feedback summarizer agent
SUMMARIZER_INSTRUCTIONS = """
You are a feedback summarizer. 
Given a piece of raw customer feedback, produce a single concise, neutral sentence
that captures the core point. No opinions, no formatting — just the summary sentence.
""".strip()
#classifying customer feedback into categories
CLASSIFIER_INSTRUCTIONS = """
You are a feedback classifier. 
Given a summary of customer feedback, respond with exactly one of:
  Positive
  Negative
  Feature Request
No explanation — just the label.
""".strip()
#recommending follow-up actions based on feedback classification
ACTION_INSTRUCTIONS = """
You are a customer success agent. 
Given a feedback classification, recommend a single concrete follow-up action
in one sentence. Be specific and actionable.
""".strip()

# ============================================================
# Customer feedback to process
# ============================================================
#input feedback the agent pipeline will process
FEEDBACK = """
I use the dashboard every day to monitor metrics, and it works well overall.
But when I'm working late at night, the bright screen is really harsh on my eyes.
If you added a dark mode option, it would make the experience much more comfortable.
"""

# ============================================================
# Helper: run one agent on a message and return its reply
# ============================================================

def run_agent(client: AgentsClient, agent_id: str, user_message: str) -> str:
    """Create a fresh thread, send user_message, run the agent, return reply text."""

    run = client.create_thread_and_process_run(
        agent_id=agent_id,
        thread=AgentThreadCreationOptions(
            messages=[
                ThreadMessageOptions(role=MessageRole.USER, content=user_message)
            ]
        ),
    )

    if run.status != RunStatus.COMPLETED:
        raise RuntimeError(f"Run ended with status: {run.status}")

    messages = client.messages.list(thread_id=run.thread_id)
    for msg in messages:
        if msg.role == MessageRole.AGENT:
            for block in msg.content:
                if block.type == "text":
                    return block.text.value.strip()

    raise RuntimeError("No agent response found in thread messages.")


# ============================================================
# Main pipeline
# ============================================================

def main():
    client = AgentsClient(
        endpoint=FOUNDRY_PROJECT_ENDPOINT,
        credential=InteractiveBrowserCredential(tenant_id=TENANT_ID),
    )

    print("=" * 60)
    print("MULTI-AGENT CUSTOMER FEEDBACK PIPELINE")
    print("Azure AI Agent Framework")
    print("=" * 60)
    print(f"\nOriginal Feedback:\n{FEEDBACK.strip()}\n")

    # ── Create agents ────────────────────────────────────────
    print("Creating agents...")
    summarizer = client.create_agent(
        model=DEPLOYMENT,
        name="summarizer",
        instructions=SUMMARIZER_INSTRUCTIONS,
    )
    classifier = client.create_agent(
        model=DEPLOYMENT,
        name="classifier",
        instructions=CLASSIFIER_INSTRUCTIONS,
    )
    action_agent = client.create_agent(
        model=DEPLOYMENT,
        name="action",
        instructions=ACTION_INSTRUCTIONS,
    )
    print(f"  ✓ summarizer  ({summarizer.id})")
    print(f"  ✓ classifier  ({classifier.id})")
    print(f"  ✓ action      ({action_agent.id})\n")

    try:
        # ── Step 1: Summarize ────────────────────────────────
        print("-" * 60)
        print("STEP 1 — Summarizer Agent")
        print("-" * 60)
        summary = run_agent(client, summarizer.id, f"Customer feedback:\n{FEEDBACK}")
        print(f"Summary: {summary}\n")

        # ── Step 2: Classify ─────────────────────────────────
        print("-" * 60)
        print("STEP 2 — Classifier Agent")
        print("-" * 60)
        classification = run_agent(client, classifier.id, summary)
        print(f"Classification: {classification}\n")

        # ── Step 3: Recommend action ─────────────────────────
        print("-" * 60)
        print("STEP 3 — Action Agent")
        print("-" * 60)
        action = run_agent(client, action_agent.id, classification)
        print(f"Recommended Action: {action}\n")

        # ── Final summary ────────────────────────────────────
        print("=" * 60)
        print("PIPELINE COMPLETE")
        print("=" * 60)
        print(f"  Summary        : {summary}")
        print(f"  Classification : {classification}")
        print(f"  Action         : {action}")

    finally:
        # ── Cleanup ──────────────────────────────────────────
        print("\nCleaning up agents...")
        for agent in [summarizer, classifier, action_agent]:
            client.delete_agent(agent.id)
            print(f"  Deleted: {agent.name} ({agent.id})")


if __name__ == "__main__":
    main()
