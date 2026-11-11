"""
Demo 6: Multi-Remote-Agent with A2A Protocol (open standard protocol for agent-to-agent communication)


Goal:   Build two remote agents that communicate using the open
        Agent-to-Agent (A2A) protocol — an industry standard for
        discoverable, interoperable AI agents over HTTP.

Context: A2A complements MCP.  MCP gives agents access to tools/data.
         A2A lets agents discover *each other* and delegate whole tasks.
         Any language, any framework — the protocol is the contract.

Key concepts:
  - Agent Card:   /.well-known/agent.json — machine-readable agent metadata
  - Task:         A JSON-RPC 2.0 message routed from host to remote agent
  - Host Agent:   Orchestrates by discovering and calling remote agents

Architecture:
         [Host / Routing Agent]
               |           |
         A2A POST      A2A POST
          (JSON-RPC)   (JSON-RPC)
               |           |
      [Title Agent]   [Outline Agent]
       :8001            :8002
       Azure AI          Azure AI

Flow:
  1. Host discovers each agent's capabilities via its Agent Card
  2. Host sends a task to the Title Agent  -> gets a blog title
  3. Host sends that title to the Outline Agent -> gets a full outline

Usage:
    python 6_A2A_MultiAgent.py
"""

import json
import os
import threading #used to run multiple HTTP servers concurrently for the remote agents
import uuid #used to generate unique IDs for JSON-RPC tasks
from http.server import BaseHTTPRequestHandler, HTTPServer #used to create the HTTP servers for the remote agents

import httpx #used to make HTTP requests to other agents in the A2A protocol
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

ENDPOINT = os.getenv("AZURE_AI_ENDPOINT", "").rstrip("/")
API_KEY  = os.getenv("AZURE_AI_KEY")
MODEL    = os.getenv("AZURE_AI_MODEL", "gpt-4o-mini")

TITLE_PORT   = 8001
OUTLINE_PORT = 8002

SEP  = "-" * 64
SEP2 = "=" * 64


# ---------------------------------------------------------------------------
# Agent Cards  — the A2A discovery document for each remote agent
# ---------------------------------------------------------------------------

TITLE_AGENT_CARD = {
    "name": "Title Agent",
    "description": "Generates a single catchy blog title for a given topic.",
    "url": f"http://localhost:{TITLE_PORT}/",
    "version": "1.0.0",
    "defaultInputModes": ["text"],
    "defaultOutputModes": ["text"],
    "capabilities": {},
    "skills": [
        {
            "id": "generate_blog_title",
            "name": "Generate Blog Title",
            "description": "Produces one clear, catchy blog title for a topic.",
            "tags": ["title", "writing"],
            "examples": ["Give me a title for an article about Azure AI Search"],
        }
    ],
}

OUTLINE_AGENT_CARD = {
    "name": "Outline Agent",
    "description": "Produces a detailed article outline from a blog title.",
    "url": f"http://localhost:{OUTLINE_PORT}/",
    "version": "1.0.0",
    "defaultInputModes": ["text"],
    "defaultOutputModes": ["text"],
    "capabilities": {},
    "skills": [
        {
            "id": "generate_outline",
            "name": "Generate Article Outline",
            "description": "Creates a structured outline (sections + bullet points) from a title.",
            "tags": ["outline", "writing"],
            "examples": ["Create an outline for: Building AI Agents with Azure"],
        }
    ],
}


# ---------------------------------------------------------------------------
# Azure AI helper (called inside each remote agent's request handler)
# ---------------------------------------------------------------------------
# This helper function wraps the Azure AI call, making it easy for each agent to invoke the model with specific instructions and user input.
def call_azure_ai(instructions: str, user_input: str) -> str:
    client = OpenAI(base_url=ENDPOINT, api_key=API_KEY)
    response = client.responses.create(
        model=MODEL,
        instructions=instructions,
        input=user_input,
    )
    return response.output_text


# ---------------------------------------------------------------------------
# Generic A2A HTTP handler — implements the two required A2A endpoints
# ---------------------------------------------------------------------------
# this class provides a generic HTTP handler for A2A-compliant agents, implementing both the discovery and task execution endpoints.
class A2AHandler(BaseHTTPRequestHandler):
    """
    Handles the two A2A HTTP endpoints every compliant agent must expose:

      GET  /.well-known/agent.json   Agent Card  (discovery)
      POST /                          JSON-RPC    (task execution)
    """
    # The agent_card and instructions attributes will be set by each specific agent subclass to define its capabilities and behavior.
    agent_card: dict = {} #dict representing the agent's capabilities and metadata
    instructions: str = "" #instructions to guide the agent's behavior when handling tasks

    def log_message(self, fmt, *args): #override to suppress default HTTP access log
        # Suppress default HTTP access log to keep demo output clean
        pass

    # -- Discovery endpoint --------------------------------------------------

    def do_GET(self): #handle the discovery endpoint for the agent
        if self.path == "/.well-known/agent.json":
            body = json.dumps(self.agent_card, indent=2).encode() #encode the agent card as JSON for the HTTP response
            self.send_response(200) #send HTTP 200 OK response
            self.send_header("Content-Type", "application/json") #set content type to JSON
            self.send_header("Content-Length", str(len(body))) #set content length header
            self.end_headers() #end HTTP headers
            self.wfile.write(body) #write the JSON-encoded agent card to the HTTP response
        else:
            self.send_response(404) #send HTTP 404 Not Found response for unknown paths
            self.end_headers() #end HTTP headers

    # -- Task execution endpoint ---------------------------------------------

    def do_POST(self): #handle the task execution endpoint for the agent
        length = int(self.headers.get("Content-Length", 0)) #get the length of the incoming HTTP request body
        raw    = self.rfile.read(length) #read the raw HTTP request body
        request = json.loads(raw) #parse the JSON-RPC request from the body

        # Extract user text from A2A message parts
        user_text = "" #initialize user text to empty string
        try:
            parts = request["params"]["message"]["parts"] #extract message parts from the A2A request
            user_text = " ".join(
                p["text"] for p in parts if p.get("kind") == "text" #concatenate all text parts from the message, ignoring non-text parts
            )
        except (KeyError, TypeError):
            pass #ignore errors if the expected structure is not present

        # Delegate to Azure AI
        result_text = call_azure_ai(self.instructions, user_text) #call Azure AI with the system prompt and user text to get the result

        # Return an A2A JSON-RPC 2.0 response with an artifact (task result)
        body = json.dumps({
            "jsonrpc": "2.0", #
            "id": request.get("id"), #echo the request ID in the response
            "result": {
                "id": str(uuid.uuid4()), #generate a unique ID for the task result
                "status": {"state": "completed"}, #mark the task as completed
                "artifacts": [
                    {"parts": [{"kind": "text", "text": result_text}]} #include the result text as an artifact
                ],
            },
        }).encode() #encode the response as JSON bytes

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


# ---------------------------------------------------------------------------
# Concrete agent handler classes — each with its own card + system prompt
# ---------------------------------------------------------------------------

def make_title_handler():
    class TitleHandler(A2AHandler):
        agent_card   = TITLE_AGENT_CARD
        instructions = (
            "You are a technical blog post title specialist. "
            "Given a topic, output exactly ONE clear and catchy blog title. "
            "Keep it under 70 characters. No markdown. No numbering. Just the title."
        )
    return TitleHandler #return the concrete handler class for the title agent


def make_outline_handler():
    class OutlineHandler(A2AHandler):
        agent_card   = OUTLINE_AGENT_CARD
        instructions = (
            "You are a technical article outline specialist. "
            "Given a blog title, produce a structured outline a developer can follow. "
            "Include: Introduction, 4-6 sections each with 3-4 bullet points, Conclusion."
        )
    return OutlineHandler #return the concrete handler class for the outline agent


# ---------------------------------------------------------------------------
# Server launcher — each agent runs in a daemon thread
# ---------------------------------------------------------------------------

def start_agent_server(port: int, handler_class) -> HTTPServer:
    server = HTTPServer(("localhost", port), handler_class)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


# ---------------------------------------------------------------------------
# Host agent — A2A client side
# ---------------------------------------------------------------------------

def discover_agent(base_url: str) -> dict:
    """
    Fetch the Agent Card from /.well-known/agent.json.
    This is how a host agent learns what a remote agent can do.
    """
    card_url = base_url.rstrip("/") + "/.well-known/agent.json"
    r = httpx.get(card_url, timeout=10) #fetch the agent card from the well-known URL
    r.raise_for_status()
    return r.json()


def send_task(agent_url: str, text: str) -> str:
    """
    Send a task to a remote agent using A2A JSON-RPC 2.0 (method: message/send).
    Returns the text from the first artifact in the response.
    agent_url: URL of the remote agent's message endpoint
    text: the task text to send
    """
    message_id = str(uuid.uuid4())
    payload = {
        "jsonrpc": "2.0",
        "id": message_id,
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": text}],
                "messageId": message_id,
            }
        },
    }

    r = httpx.post(agent_url, json=payload, timeout=30) #send the JSON-RPC request to the agent
    r.raise_for_status() #raise an exception if the request failed
    data = r.json() #parse the JSON response

    artifacts = data.get("result", {}).get("artifacts", [])
    if artifacts:
        parts = artifacts[0].get("parts", [])
        return " ".join(p.get("text", "") for p in parts if p.get("kind") == "text")
    return "(no response)"


# ---------------------------------------------------------------------------
# Main — orchestrates the full A2A flow
# ---------------------------------------------------------------------------

def main():
    os.system("cls" if os.name == "nt" else "clear")
    print(SEP2)
    print("  Demo 6: Multi-Remote-Agent with A2A Protocol")
    print("  JSON-RPC over HTTP  |  Agent Cards  |  Azure AI Foundry")
    print(SEP2)
    print()

    # --- Launch remote agent servers ----------------------------------------
    print("  Launching remote agent servers...")
    title_server   = start_agent_server(TITLE_PORT,   make_title_handler())
    outline_server = start_agent_server(OUTLINE_PORT, make_outline_handler())
    print(f"    [Title Agent]   http://localhost:{TITLE_PORT}/")
    print(f"    [Outline Agent] http://localhost:{OUTLINE_PORT}/")
    print()

    topic = "Building AI agents with the A2A protocol and Azure AI Foundry"

    # --- Step 1: Discover agents via their Agent Cards ----------------------
    print(SEP)
    print("  Step 1: Discover remote agents via Agent Cards")
    print(f"          GET /.well-known/agent.json") #log the endpoint used to fetch the agent card
    print(SEP)

    title_card   = discover_agent(f"http://localhost:{TITLE_PORT}/")
    outline_card = discover_agent(f"http://localhost:{OUTLINE_PORT}/")

    for card in (title_card, outline_card):
        print(f"\n  Agent : {card['name']}  (v{card['version']})")
        print(f"  URL   : {card['url']}")
        for skill in card.get("skills", []):
            print(f"  Skill : {skill['name']}")
            print(f"          {skill['description']}")

    # --- Step 2: Route task to Title Agent ----------------------------------
    print(f"\n{SEP}")
    print("  Step 2: Send task to Title Agent")
    print(f"          POST http://localhost:{TITLE_PORT}/  (message/send)") #print the endpoint used to send the task to the Title Agent
    print(SEP)
    print(f"\n  Topic  : {topic}")
    print("  Waiting for Title Agent...\n")

    # Send the task to the Title Agent and wait for the response. send_task handles the HTTP request and returns the result.
    title = send_task(
        f"http://localhost:{TITLE_PORT}/",
        f"Generate a blog title for: {topic}",
    )
    print(f"  Title  : {title}")

    # --- Step 3: Route title to Outline Agent -------------------------------
    print(f"\n{SEP}")
    print("  Step 3: Send title to Outline Agent")
    print(f"          POST http://localhost:{OUTLINE_PORT}/  (message/send)") #print the endpoint used to send the task to the Outline Agent
    print(SEP)
    print(f"\n  Title  : {title}")
    print("  Waiting for Outline Agent...\n")

    outline = send_task(f"http://localhost:{OUTLINE_PORT}/", title)

    print("  Outline:")
    print()
    for line in outline.splitlines():
        print(f"    {line}")

    # --- Summary ------------------------------------------------------------
    print(f"\n{SEP2}")
    print("  COMPLETE - A2A Protocol Flow Summary")
    print(SEP2)
    print()
    print("  1. [Discovery]  Host fetched each agent's card at:")
    print("                  /.well-known/agent.json")
    print()
    print("  2. [Task: Title]  Host -> Title Agent  (JSON-RPC message/send)")
    print(f"                   Input:  {topic[:60]}...")
    print(f"                   Output: {title}")
    print()
    print("  3. [Task: Outline]  Host -> Outline Agent  (JSON-RPC message/send)")
    print("                      Input:  title from step 2")
    print("                      Output: full article outline")
    print()
    print("  Each agent ran independently over HTTP - no shared memory,")
    print("  no shared code. The A2A protocol is the only contract.")
    print(SEP2)
    print()

    title_server.shutdown()
    outline_server.shutdown()


if __name__ == "__main__":
    main()
