import os
from openai import AzureOpenAI, OpenAI
from dotenv import load_dotenv

load_dotenv()

LLMClient = OpenAI | AzureOpenAI


def create_openai_client(api_key: str | None = None) -> OpenAI:
    """Return a standard OpenAI client.

    The API key is read from the OPENAI_API_KEY environment variable by
    default. Pass *api_key* explicitly to override it.
    """
    resolved_key = api_key or os.environ.get("OPENAI_API_KEY")
    if not resolved_key:
        raise ValueError(
            "OpenAI API key not found. "
            "Set the OPENAI_API_KEY environment variable or pass it explicitly."
        )
    return OpenAI(api_key=resolved_key)


def create_azure_openai_client(
    api_key: str | None = None,
    azure_endpoint: str | None = None,
    api_version: str | None = None,
) -> AzureOpenAI:
    """Return an Azure OpenAI client.

    Parameters are resolved from explicit arguments first, then from the
    environment variables AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT and
    OPENAI_API_VERSION.
    """
    resolved_key = api_key or os.environ.get("AZURE_OPENAI_API_KEY")
    resolved_endpoint = azure_endpoint or os.environ.get("AZURE_OPENAI_ENDPOINT")
    resolved_version = api_version or os.environ.get("OPENAI_API_VERSION")

    if not resolved_key:
        raise ValueError(
            "Azure OpenAI API key not found. "
            "Set the AZURE_OPENAI_API_KEY environment variable or pass it explicitly."
        )
    if not resolved_endpoint:
        raise ValueError(
            "Azure OpenAI endpoint not found. "
            "Set the AZURE_OPENAI_ENDPOINT environment variable or pass it explicitly."
        )
    if not resolved_version:
        raise ValueError(
            "Azure OpenAI API version not found. "
            "Set the OPENAI_API_VERSION environment variable or pass it explicitly."
        )

    return AzureOpenAI(
        api_key=resolved_key,
        azure_endpoint=resolved_endpoint,
        api_version=resolved_version,
    )
