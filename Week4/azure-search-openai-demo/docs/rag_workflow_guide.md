# RAG Chatbot Workflow: A Simple Guide

This guide explains what happens behind the scenes when you add documents and ask the chatbot a question. The diagrams use plain text and arrows, not Mermaid.

## Where Things Run

```text
YOUR COMPUTER                                      AZURE
+-----------------------------+                    +---------------------------+
| Browser                     |                    | Azure OpenAI              |
| React chat screen            |  sends requests    | Chat model and embeddings |
| Quart Python backend         | -----------------> | Azure AI Search            |
| Ingestion and text chunking  |                    | Blob Storage               |
+-----------------------------+                    +---------------------------+
```

When developing locally, the browser, React app, and Python backend run on your computer. The model, search index, and document storage are Azure services by default. When deployed, the backend moves to Azure too. The services and models used are selected by the project's environment settings.

## What Happens When You Ask a Question

```text
 YOU                         YOUR COMPUTER                                AZURE
  |                                |                                         |
  | 1. Type a question             |                                         |
  +------------------------------> |                                         |
  |                          2. React packages the question,                 |
  |                             chat history, and settings                   |
  |                                |                                         |
  |                          3. API sends it to the Python backend           |
  |                                |                                         |
  |                          4. Backend asks the chat model to                |
  |                             rewrite the question for searching            |
  |                                +---------------------------------------> |
  |                                |              rewritten query             |
  |                                | <---------------------------------------+
  |                          5. Backend asks Search for matching text          |
  |                             and/or vector results                         |
  |                                +---------------------------------------> |
  |                                |              relevant chunks             |
  |                                | <---------------------------------------+
  |                          6. Backend builds a prompt with your              |
  |                             question and the matching document text       |
  |                                +---------------------------------------> |
  |                                |              grounded answer             |
  |                                | <---------------------------------------+
  |                          7. Backend streams the answer and citations       |
  |                                |                                         |
  | 8. See the answer and sources  |                                         |
  | <------------------------------+                                         |
```

| Step | Code or service | What it does |
| --- | --- | --- |
| 1-2. Prepare the question | [Chat.tsx](../app/frontend/src/pages/chat/Chat.tsx) | Adds conversation history and selected options, such as retrieval mode, filters, or number of search results. |
| 3. Send it to the backend | [api.ts](../app/frontend/src/api/api.ts) | Sends the request to `/chat/stream` (normally) or `/chat`. |
| 4. Receive and route it | [app.py](../app/backend/app.py) | The Quart API checks the request and passes it to the chat approach. |
| 5. Rewrite for search | [chatreadretrieveread.py](../app/backend/approaches/chatreadretrieveread.py), [approach.py](../app/backend/approaches/approach.py), [query_rewrite.system.jinja2](../app/backend/approaches/prompts/query_rewrite.system.jinja2) | Builds a focused search query from the latest question and earlier conversation. The chat model runs in Azure by default. |
| 6. Find useful passages | [approach.py](../app/backend/approaches/approach.py), Azure AI Search | Searches the index for matching document chunks. Depending on settings, it uses text search, vector search, or both. It can also apply category filters and semantic ranking. |
| 7. Prepare evidence and answer | [approach.py](../app/backend/approaches/approach.py), [chat_answer.system.jinja2](../app/backend/approaches/prompts/chat_answer.system.jinja2), [chat_answer.user.jinja2](../app/backend/approaches/prompts/chat_answer.user.jinja2) | Adds retrieved text and source references to a prompt. The Azure-hosted chat model writes an answer using that evidence. |
| 8. Show the result | [app.py](../app/backend/app.py), [Chat.tsx](../app/frontend/src/pages/chat/Chat.tsx), [Answer.tsx](../app/frontend/src/components/Answer/Answer.tsx) | The backend sends response pieces as they are generated. The browser displays the answer and citations. |

**The important idea:** the model is not given every document. Search first finds a small set of relevant chunks, and those chunks are sent to the model as context. Citations point back to the source documents.

## What Happens Before Chat: Add Documents to Search

Documents must be processed and indexed before the chatbot can retrieve them.

```text
DOCUMENTS             YOUR COMPUTER                                  AZURE
    |                       |                                            |
    | 1. Put files in data/ |                                            |
    +---------------------> |                                            |
                       2. Run prepdocs.ps1                               |
                       3. Read and parse each file                       |
                          (locally or with Document Intelligence)         |
                       4. Break text into smaller chunks                 |
                          so search can find relevant sections           |
                       5. Ask the embedding model for vectors             |
                          (if vector search is enabled)                  |
                           |                 |                            |
                           | original files  | chunks and vectors         |
                           +---------------->|--------------------------> |
                                             |                  Blob      |
                                             |                  Storage  |
                                             |                  AI Search|
                                             |                            |
```

1. Put source files in `data/` (or provide another path) and run [prepdocs.ps1](../scripts/prepdocs.ps1).
2. The script starts [prepdocs.py](../app/backend/prepdocs.py), which selects how the files will be processed.
3. [filestrategy.py](../app/backend/prepdocslib/filestrategy.py) uploads original files to Azure Blob Storage and processes each file. Local parsers read supported formats; Azure Document Intelligence can extract text and layout from more complex formats.
4. [fileprocessor.py](../app/backend/prepdocslib/fileprocessor.py) connects the selected parser with a chunking strategy. [textsplitter.py](../app/backend/prepdocslib/textsplitter.py) breaks long text into smaller, slightly overlapping passages.
5. When vector search is enabled, [embeddings.py](../app/backend/prepdocslib/embeddings.py) sends chunks to the configured embedding model. The model returns numeric vectors that represent the text's meaning.
6. [searchmanager.py](../app/backend/prepdocslib/searchmanager.py) writes chunk text, source information, and any vectors to Azure AI Search. The chatbot searches this index later.

The parsing and chunking steps run locally in the manual-ingestion mode. Azure services still handle Azure Document Intelligence (if selected), embeddings (by default), Blob Storage, and the search index.

## Optional: Cloud Ingestion

Cloud ingestion is an alternate way to prepare documents. Instead of running most processing on your computer, Azure AI Search's indexer coordinates Azure Functions:

```text
Azure Blob Storage
        |
        v
Azure AI Search indexer
        |
        +--> document_extractor Function: extract text and figure locations
        |
        +--> figure_processor Function: optionally describe figures
        |
        +--> Shaper skill: combine extracted text and figure information
        |
        +--> text_processor Function: create chunks and optional embeddings
        |
        v
Azure AI Search index
```

This path is configured by [setup_cloud_ingestion.py](../app/backend/setup_cloud_ingestion.py). It is optional; the manual `prepdocs.ps1` flow is the usual local development path. Both ingestion modes prepare the index that the chat workflow searches.

## Optional Features

- **Agentic retrieval:** When enabled, the backend can ask an Azure AI Search Knowledge Base to plan retrieval. Depending on configuration, it may also use web or SharePoint sources. This replaces the normal rewrite-and-search steps.
- **Images:** Multimodal settings can add figure descriptions or image data to indexed content and answers. Image processing can call Azure vision services and may store images in Blob Storage.
- **Chat history:** Conversation history can stay in the browser or, when configured, be persisted in Azure Cosmos DB.
- **Local model:** This example's default model and embedding calls are remote. Local execution of the app does not mean local LLM inference.
