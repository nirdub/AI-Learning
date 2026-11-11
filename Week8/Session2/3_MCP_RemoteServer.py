"""
Demo 3: Connecting an Agent to a Remote MCP Server

Goal:   Build an agent that looks up Azure technical documentation
        dynamically using Microsoft Learn's public MCP server.

Context: Instead of baking documentation into the system prompt,
         we give the agent a live connection to the source of truth.
         The agent discovers tools at runtime via MCPTool, and the
         Azure AI Foundry Responses API handles the approval flow.

Key takeaway:
         AI agents can seamlessly fetch trusted, external data
         if given the right server endpoint and tool approval logic.

Architecture:
         [ AIProjectClient ]  --MCPTool-->  [ MS Learn MCP Server ]
         [ Responses API   ]  <--output--   [ learn.microsoft.com ]

Usage:
    python 3_MCP_RemoteServer.py
"""

import os
from dotenv import load_dotenv

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient #client to interact with Azure AI Projects service
from azure.ai.projects.models import PromptAgentDefinition, MCPTool #models for defining agents and MCP tools
from openai.types.responses.response_input_param import McpApprovalResponse #model for responding to MCP approval requests

load_dotenv()

PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT")
MODEL_DEPLOYMENT = os.getenv("MODEL_DEPLOYMENT_NAME", "gpt-4o-mini")

MS_LEARN_MCP_URL = "https://learn.microsoft.com/api/mcp" #this is public mcp server of microsoft

SEP = "-" * 64

#creating agent function
def run_agent(openai_client, agent, user_query: str):
    print(f"\n{SEP}")
    print(f"  User question: {user_query}")
    print(SEP)

    # Create a conversation thread
    conversation = openai_client.conversations.create()

    # Send the initial request
    response = openai_client.responses.create(
        conversation=conversation.id,
        input=user_query,
        extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},#pass agent reference to the request
    )

    # Process any MCP approval requests in a loop. Foundry will ask for approval to use mcp tool but in this case if server req starts with api-specs and item.id is there then auto approve the request but we can involve human in between ex for critical ones
    while True:
        input_list = []
        for item in response.output:
            if item.type == "mcp_approval_request":
                if item.server_label == "api-specs" and item.id: # auto-approve requests for the api-specs server if an ID is present
                    print(f"\n  [Approval] Approving MCP tool call: {item.name}")
                    input_list.append(
                        McpApprovalResponse(
                            type="mcp_approval_response",
                            approve=True,
                            approval_request_id=item.id,
                        )
                    )

        if not input_list:
            break

        response = openai_client.responses.create(
            input=input_list,
            previous_response_id=response.id,
            extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
        )

    print(f"\n{SEP}")
    print("  AGENT ANSWER:")
    print(SEP)
    print(response.output_text)
    print()


def main():
    os.system("cls" if os.name == "nt" else "clear")
    print("=" * 64)
    print("  Demo 3: Agent + Remote MCP Server")
    print("  Connecting to Microsoft Learn documentation")
    print("=" * 64)
    print()

    queries = [
        "What is Azure AI Search and what are its main pricing tiers?",
        "How do I enable semantic search on an Azure AI Search index?",
    ]

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(endpoint=PROJECT_ENDPOINT, credential=credential) as project_client,
        project_client.get_openai_client() as openai_client,
    ):
        # Create the agent with an MCPTool pointed at MS Learn
        mcp_tool = MCPTool(
            server_label="api-specs",
            server_url=MS_LEARN_MCP_URL,
            require_approval="always", #tool usage approval
        )

        agent = project_client.agents.create_version(
            agent_name="MsLearnAgent",
            definition=PromptAgentDefinition(
                model=MODEL_DEPLOYMENT,
                instructions=(
                    "You are a helpful Azure documentation assistant. "
                    "Use the available MCP tools to look up accurate, up-to-date "
                    "information from Microsoft Learn documentation. "
                    "Always cite which docs you consulted."
                ),
                tools=[mcp_tool],
            ),
        )
        print(f"  Agent created: {agent.name} (version {agent.version})")
        print()
        print("  The agent will use MCP to query live Azure docs.")
        print("  No static docs are embedded in the system prompt.")
        print()

        try:
            for query in queries:
                run_agent(openai_client, agent, query)
                input("  Press Enter for next query...")
                print()
        finally:
            project_client.agents.delete_version(agent_name=agent.name, agent_version=agent.version)
            print("  Agent deleted.")

    print("=" * 64)
    print("  Key Concept:")
    print("  The agent never hardcoded any docs. It discovered available")
    print("  tools from the MCP server at runtime, called them, and")
    print("  grounded its answers in the live documentation.")
    print("=" * 64)
    print()


if __name__ == "__main__":
    main()
