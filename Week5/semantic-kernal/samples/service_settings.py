# Copyright (c) Microsoft. All rights reserved.
# Semantic Kernel sample helper - ServiceSettings

import os

from dotenv import load_dotenv

load_dotenv()


class ServiceSettings:
    """Reads LLM service configuration from environment variables / .env file."""

    def __init__(self):
        self.global_llm_service = os.getenv("GLOBAL_LLM_SERVICE")

        # OpenAI
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_org_id = os.getenv("OPENAI_ORG_ID")
        self.openai_chat_model_id = os.getenv("OPENAI_CHAT_MODEL_ID")
        self.openai_text_model_id = os.getenv("OPENAI_TEXT_MODEL_ID")
        self.openai_embedding_model_id = os.getenv("OPENAI_EMBEDDING_MODEL_ID")

        # Azure OpenAI
        self.azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_openai_chat_deployment_name = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")
        self.azure_openai_text_deployment_name = os.getenv("AZURE_OPENAI_TEXT_DEPLOYMENT_NAME")
        self.azure_openai_embedding_deployment_name = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")
        self.azure_openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION")
