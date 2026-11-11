"""
Demo 4: Agent + Custom MCP Server — Inventory Assistant

An AI agent backed by a custom MCP server (inventory_server.py).
The agent discovers the server's tools at runtime and uses them
to answer any inventory question you ask in the chat loop.

Key concept:
    Your private Python logic (the inventory dict) is never
    exposed directly to the AI. All data flows through the MCP
    protocol — structured and controlled by the server you built.
    The Azure AI Foundry Responses API handles the function call loop.

Architecture:
    [ AIProjectClient ]  --FunctionTool-->  [ inventory_server.py ]
    [ Responses API   ]  <--tool result--   [ (FastMCP server)    ]

Usage:
    python 4_MCP_CustomInventory.py
"""

import asyncio #asyncio is used for asynchronous programming, allowing us to run the chat loop and server connection concurrently
import json
import os
import sys
from contextlib import AsyncExitStack #AsyncExitStack allows us to manage multiple asynchronous context managers (like the server connection) cleanly
from dotenv import load_dotenv

from mcp import ClientSession, StdioServerParameters #MCP client session and server parameters for connecting to the inventory server
from mcp.client.stdio import stdio_client #stdio client for connecting to the MCP server via standard input/output
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient 
from azure.ai.projects.models import PromptAgentDefinition, FunctionTool #models for defining agents and their function tools
from openai.types.responses.response_input_param import FunctionCallOutput #model for handling function call outputs from the AI agent

load_dotenv()

PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT")
MODEL_DEPLOYMENT = os.getenv("MODEL_DEPLOYMENT_NAME", "gpt-4o-mini")

# Connect to the inventory server and start the chat loop with the AI agent.
# This async function will handle the asynchronous connection and interaction with the server
async def connect_to_server(exit_stack: AsyncExitStack):
    """Start inventory_server.py as a subprocess and return an MCP session and tools."""
    server_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inventory_server.py")

    # Define the parameters for connecting to the inventory server via standard input/output
    server_params = StdioServerParameters(
        command=sys.executable, #use the current Python interpreter to run the server script
        args=[server_script], #pass the server script as an argument to the Python interpreter
        env=None, #use the default environment variables for the server process
    )
    # Establish the connection to the server using the defined parameters using the stdio client and manage it with the exit stack
    stdio_transport = await exit_stack.enter_async_context(stdio_client(server_params)) 
    stdio, write = stdio_transport #unpack the standard input/output streams from the transport
    session = await exit_stack.enter_async_context(ClientSession(stdio, write)) #create and manage the client session for communicating with the server
    await session.initialize() #initialize the client session to prepare for communication with the server

    response = await session.list_tools() #retrieve the list of available tools from the server
    tools = response.tools #extract the list of tools from the response
    print("\nConnected to server with tools:", [tool.name for tool in tools])

    return session, tools


async def chat_loop(session: ClientSession, tools):
    """Interactive chat loop — ask the inventory agent anything."""

    with (
        DefaultAzureCredential() as credential, #Azure credential for authenticating with the AI project
        AIProjectClient(endpoint=PROJECT_ENDPOINT, credential=credential) as project_client, #client for interacting with the Azure AI project
        project_client.get_openai_client() as openai_client, #OpenAI client for making requests to the deployed model
    ):
        # Build a callable for each MCP tool. These callables will be used to invoke the corresponding tool on the server.
        def make_tool_func(tool_name):
            async def tool_func(**kwargs): #function to call the corresponding MCP tool on the server with the provided arguments
                return await session.call_tool(tool_name, kwargs) #call the tool on the server with the provided arguments
            tool_func.__name__ = tool_name #set the function name to match the tool name for easier identification
            return tool_func
        
        # Create a dictionary mapping tool names to their corresponding callables for easy access
        functions_dict = {tool.name: make_tool_func(tool.name) for tool in tools}

        # Wrap MCP tools as FunctionTool definitions for the agent
        mcp_function_tools = []
        for tool in tools:
            mcp_function_tools.append(FunctionTool(
                name=tool.name,
                description=tool.description,
                parameters={
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                },
                strict=True,
            ))

        # Create the agent with inventory-specific instructions
        agent = project_client.agents.create_version(
            agent_name="inventory-agent",
            definition=PromptAgentDefinition(
                model=MODEL_DEPLOYMENT,
                instructions=(
                    "You are an inventory assistant. Here are some general guidelines:\n"
                    "- Recommend restock if item inventory < 10 and weekly sales > 15\n"
                    "- Recommend clearance if item inventory > 20 and weekly sales < 5"
                ),
                tools=mcp_function_tools,
            ),
        )
        print(f"  Agent created: {agent.name} (version {agent.version})")
        print()

        try:
            while True:
                user_input = input("\nEnter a prompt for the inventory agent (or 'quit' to exit).\nUSER: ").strip()
                if user_input.lower() == "quit":
                    print("Exiting chat.")
                    break

                # Send initial request via Responses API
                response = openai_client.responses.create(
                    input=user_input,
                    extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
                )

                # Process function calls in a loop until the agent is done
                while True:
                    input_list = []
                    for item in response.output:
                        if item.type == "function_call":
                            fn_name = item.name
                            kwargs = json.loads(item.arguments) #parse the JSON arguments for the function call into a Python dictionary
                            print(f"\n  [Tool] {fn_name}({json.dumps(kwargs) if kwargs else ''})") #log the tool call with its arguments

                            result = await functions_dict[fn_name](**kwargs) #invoke the tool function with the parsed arguments
                            tool_output = result.content[0].text if result.content else "{}"
                            print(f"  [Result] {tool_output[:300]}")

                            # Append the tool call output to the input list for the next request to the agent
                            input_list.append(FunctionCallOutput(
                                type="function_call_output",
                                call_id=item.call_id,
                                output=tool_output,
                            ))
                    # If there are any tool call outputs, send them back to the agent for further processing
                    if input_list:
                        response = openai_client.responses.create(
                            input=input_list,
                            previous_response_id=response.id,
                            extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
                        )
                    else:
                        break

                print(f"\nASSISTANT: {response.output_text}")

        finally:
            project_client.agents.delete_version(agent_name=agent.name, agent_version=agent.version)
            print("Agent deleted.")


async def main():
    os.system("cls" if os.name == "nt" else "clear")
    print("=" * 64)
    print("  Demo 4: Agent + Custom MCP Inventory Server")
    print("=" * 64)
    print()
    print("  Starting inventory_server.py via stdio transport...")
    print()

    exit_stack = AsyncExitStack() #manage the lifecycle of asynchronous resources, such as the connection to the inventory server
    try:
        session, tools = await connect_to_server(exit_stack) #connect to the inventory server and obtain the session and available tools
        await chat_loop(session, tools) #start the interactive chat loop with the connected session and available tools
    finally:
        await exit_stack.aclose() #close all resources managed by the exit stack, including the connection to the inventory server


if __name__ == "__main__":
    asyncio.run(main())
