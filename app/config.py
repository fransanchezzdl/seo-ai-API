"""Cliente reutilizable; Azure tiene prioridad y utiliza el nombre del deployment."""

import os
from functools import lru_cache

from dotenv import load_dotenv
from openai import AzureOpenAI, OpenAI

load_dotenv()
OPENAI_MODEL = os.getenv("AZURE_OPENAI_DEPLOYMENT") or os.getenv("OPENAI_MODEL", "gpt-4o-mini")


class ConfigurationError(RuntimeError):
    pass


@lru_cache
def get_client() -> OpenAI:
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "").strip()
    azure_key = os.getenv("AZURE_OPENAI_API_KEY", "").strip()
    if endpoint or azure_key:
        if not endpoint or not azure_key:
            raise ConfigurationError("Configura AZURE_OPENAI_ENDPOINT y AZURE_OPENAI_API_KEY")
        return AzureOpenAI(
            api_key=azure_key,
            azure_endpoint=endpoint,
            api_version=os.getenv("OPENAI_API_VERSION", "2024-10-21"),
            timeout=90.0,
            max_retries=1,
        )
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise ConfigurationError("Configura las credenciales de Azure OpenAI en .env")
    return OpenAI(api_key=key, timeout=90.0, max_retries=1)
