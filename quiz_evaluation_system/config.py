"""
Azure OpenAI Configuration Module
Loads API credentials and initializes Azure OpenAI clients
"""

import os
from openai import AzureOpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# =============================================================
# AZURE OPENAI CREDENTIALS
# =============================================================

AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")

AZURE_OPENAI_ENDPOINT = os.getenv(
    "AZURE_OPENAI_ENDPOINT",
    "https://supc-mk0vfd79-eastus2.cognitiveservices.azure.com/"
).strip()

# ------------------------------
#  Chat Model (GPT-4o-mini)
# ------------------------------
AZURE_CHAT_DEPLOYMENT = os.getenv(
    "AZURE_CHAT_DEPLOYMENT",
    "Supremology-gpt-4o-mini"
).strip()

# Newer API version for chat
AZURE_CHAT_API_VERSION = os.getenv(
    "AZURE_CHAT_API_VERSION",
    "2024-12-01-preview"
).strip()

# ------------------------------
#  Embedding Model (text-embedding-3-large)
# ------------------------------
AZURE_EMBEDDING_DEPLOYMENT = os.getenv(
    "AZURE_EMBEDDING_DEPLOYMENT",
    "Supremology-text-embedding-3-large"
).strip()

# Older embedding API version required by Azure
AZURE_EMBEDDING_API_VERSION = os.getenv(
    "AZURE_EMBEDDING_API_VERSION",
    "2024-02-01"
).strip()

# =============================================================
# INITIALIZE AZURE OPENAI CLIENTS
# =============================================================

# Chat client for quiz evaluation
chat_client = AzureOpenAI(
    api_key=AZURE_OPENAI_KEY,
    api_version=AZURE_CHAT_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)

# Embedding client (if needed for future features)
embed_client = AzureOpenAI(
    api_key=AZURE_OPENAI_KEY,
    api_version=AZURE_EMBEDDING_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)

print("✅ Azure OpenAI configuration loaded successfully")
