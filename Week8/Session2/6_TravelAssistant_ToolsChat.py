import os
import glob
from dotenv import load_dotenv
from openai import OpenAI

# -------------------------------------------------------
# Demo 6: Travel Assistant Chat — Responses API + Tools
#
# Based on: https://microsoftlearning.github.io/mslearn-ai-studio/
#           Instructions/Exercises/04a-use-own-data.html
#
# Demonstrates using the Responses API with two tools together:
#   - file_search  → retrieves answers from Margie's Travel brochures
#   - web_search   → retrieves current information from the web
#
# Conversation context is maintained across turns using
# previous_response_id so the model remembers prior exchanges.
#
# Usage:
#   python 6_TravelAssistant_ToolsChat.py
#
# Try these prompts:
#   "What's happening in San Francisco next month?"  → uses web_search
#   "What hotels does Margie's Travel offer there?"  → uses file_search
# -------------------------------------------------------

load_dotenv()

AZURE_AI_ENDPOINT = os.getenv("AZURE_AI_ENDPOINT")
AZURE_AI_KEY      = os.getenv("AZURE_AI_KEY")
MODEL_DEPLOYMENT  = os.getenv("AZURE_AI_MODEL", "gpt-4o-mini")
DOCS_FOLDER       = os.path.join(os.path.dirname(__file__), "documents")

SEP = "-" * 62

#creating vector db on azure and storing our docs over there
def create_vector_store(client: OpenAI) -> str:
    """Upload all PDFs from the documents folder to a new vector store."""
    pdf_files = glob.glob(os.path.join(DOCS_FOLDER, "*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"No PDF files found in: {DOCS_FOLDER}")

    print(f"  Uploading {len(pdf_files)} brochure(s) to vector store...")
    vector_store = client.vector_stores.create(name="margies-travel-brochures")

    file_streams = [open(f, "rb") for f in pdf_files]
    client.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vector_store.id,
        files=file_streams
    )
    for f in file_streams:
        f.close()

    print(f"  Vector store ready: {vector_store.id}")
    return vector_store.id


def main():
    os.system("cls" if os.name == "nt" else "clear")
    print("=" * 62)
    print("  Margie's Travel Assistant")
    print("  Responses API — file_search + web_search tools")
    print("=" * 62)
    print()
    
    client = OpenAI(
        base_url=AZURE_AI_ENDPOINT,
        api_key=AZURE_AI_KEY
    )

    # Build vector store from travel brochures
    vector_store_id = create_vector_store(client)

    tools = [
        {
            "type": "file_search",
            "vector_store_ids": [vector_store_id]
        },
        {
            "type": "web_search_preview"
        }
    ]

    instructions = """
    You are a helpful travel assistant for Margie's Travel.
    Use the file search tool to answer questions about destinations
    and packages from our brochures. Use web search for current
    events, weather, or information not covered in the brochures.
    Keep responses concise and friendly.
    """

    print()
    print("  Type your travel questions below. Type 'quit' to exit.")
    print(SEP)

    last_response_id = None

    while True:
        user_input = input("\n  You: ").strip()
        if user_input.lower() == "quit":
            break
        if not user_input:
            continue

        response = client.responses.create(
            model=MODEL_DEPLOYMENT,
            instructions=instructions,
            input=user_input,
            previous_response_id=last_response_id, #context of last query to maintain context of the conversation
            tools=tools
        )

        print(f"\n  Assistant: {response.output_text}")
        last_response_id = response.id

    # Clean up vector store
    print()
    print(SEP)
    print("  Cleaning up vector store...")
    client.vector_stores.delete(vector_store_id)
    print("  Done. Goodbye!")


if __name__ == "__main__":
    main()
