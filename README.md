# AI-Learning

A collection of hands-on labs and examples for learning generative AI and Azure AI services. The repository is organized by week; each folder contains independent exercises, demos, or setup guides rather than one application with a shared installation process.

## Learning path

| Folder | Topics |
| --- | --- |
| [`Week1/`](Week1/) | LLM fundamentals: local models, prompting, hallucinations, tokenization, embeddings, attention, RAG, and vector search. Start with [Week 1's guide](Week1/README.md). |
| [`Week2/`](Week2/) | Azure AI Foundry agents, function calling, and Code Interpreter data-analysis demos. See [Week 2's guide](Week2/README.md). |
| [`Week3/`](Week3/) | Prompt Flow RAG with Wikipedia and OpenTelemetry tracing for Azure OpenAI. See the [chat-wiki guide](Week3/chat-wiki/README.md) and [tracing guide](Week3/Tracing/README.md). |
| [`Week4/`](Week4/) | A complete retrieval-augmented generation (RAG) chatbot using Azure AI Search and Azure OpenAI. See [Week 4's guide](Week4/README.md) and its [student setup guide](Week4/STUDENT_SETUP_GUIDE.md). |
| [`Week5/`](Week5/) | Azure AI Content Safety and PII detection, Semantic Kernel, and multi-agent orchestration. See [Week 5's guide](Week5/README.md). |
| [`Week6/`](Week6/) | Azure AI Vision examples including OCR, image analysis, landmark and brand detection, and Custom Vision classification/object detection. See [Week 6's guide](Week6/README.md). |
| [`Week7/`](Week7/) | Azure AI Language and Speech examples, including language analysis, speech synthesis, transcription, translation, and conversational demos. See the guides in [`Week7/Session1/`](Week7/Session1/) and [`Week7/Session2/`](Week7/Session2/), plus the [TA setup guide](Week7/TA_SETUP_GUIDE.md). |
| [`Week8/`](Week8/) | Document Intelligence and Content Understanding, Azure AI Search, MCP tools, and multi-agent examples. See the guides in [`Week8/Session1/`](Week8/Session1/) and [`Week8/Session2/`](Week8/Session2/). |
| [`MS-Labs/`](MS-Labs/) | Microsoft Learn lab material for AI agents, AI Studio, and generative AI operations. |

## Getting started

1. Clone the repository and open it in your editor:
   ```bash
   git clone https://github.com/nirdub/AI-Learning.git
   cd AI-Learning
   ```
2. Choose a week or session and read its README or setup guide first. Prerequisites, dependencies, and run locations vary by exercise.
3. Where a lab requires Python, create and activate a virtual environment as described by that lab, then install its listed dependencies. There is no single repository-wide `requirements.txt` or setup command.
4. Configure only the credentials and Azure resources required by the selected exercise. Use its `.env.example` or setup guide as a reference, and keep real keys and secrets in local `.env` files or environment variables—never commit them.
5. Run commands from the working directory specified in that lab's instructions; relative file paths differ between exercises.

Many examples require access to Azure AI services, deployed models, or course-provided resources. Some exercises run locally, while others may incur Azure charges. Confirm resource availability and pricing before provisioning anything yourself, and clean up resources when finished.

## Security and credentials

Do not put API keys, connection strings, or other credentials in source files or commits. The repository includes per-exercise environment examples and ignore rules; check each lab's documentation for the exact variable names and required services.
