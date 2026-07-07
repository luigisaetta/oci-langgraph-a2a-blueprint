"""
Author: L. Saetta
Date last modified: 2026-07-07
License: MIT
Description: OpenAI-compatible Responses API client helpers for the sample agent.
Agent customization: Modify when changing the sample agent LLM integration.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import os
from typing import Any, Protocol

from dotenv import load_dotenv

DEFAULT_LLM_MODEL_ID = "openai.gpt-5.5"
DEFAULT_LLM_OCI_REGION = "us-chicago-1"
AGENT_LLM_MODEL_ID_ENV = "AGENT_LLM_MODEL_ID"
AGENT_LLM_API_KEY_ENV = "AGENT_LLM_API_KEY"
AGENT_LLM_OCI_REGION_ENV = "AGENT_LLM_OCI_REGION"
AGENT_LLM_BASE_URL_ENV = "AGENT_LLM_BASE_URL"


class LlmResponder(Protocol):
    """Minimal text response contract used by the LangGraph sample step."""

    def answer(self, input_text: str) -> str:
        """Return an LLM answer for the provided text.

        Args:
            input_text: Original user message sent to the agent.

        Returns:
            Model-generated answer text.
        """


@dataclass(frozen=True)
class LlmSettings:
    """Runtime settings for the OpenAI-compatible Responses API client.

    Attributes:
        model_id: OCI OpenAI-compatible model id.
        api_key: OCI OpenAI-compatible API key.
        base_url: OpenAI-compatible inference endpoint.
    """

    model_id: str
    api_key: str
    base_url: str


class ResponsesApiLlmClient:
    """LLM responder backed by the OpenAI-compatible Responses API.

    Args:
        client: OpenAI-compatible client instance.
        model_id: Model id passed to the Responses API.
    """

    def __init__(self, client: Any, model_id: str) -> None:
        self.client = client
        self.model_id = model_id

    def answer(self, input_text: str) -> str:
        """Return the model response for the original agent input.

        Args:
            input_text: Original user message sent to the agent.

        Returns:
            Model-generated answer text.

        Raises:
            ValueError: If the model response does not contain text.
        """
        response = self.client.responses.create(
            model=self.model_id,
            input=input_text,
        )
        return extract_response_text(response)


def create_default_llm_client() -> ResponsesApiLlmClient:
    """Create the default Responses API-backed LLM responder.

    Returns:
        Configured Responses API LLM responder.

    Raises:
        ValueError: If required LLM configuration is missing.
    """
    settings = load_llm_settings()
    return ResponsesApiLlmClient(
        client=create_openai_client(settings),
        model_id=settings.model_id,
    )


def create_openai_client(settings: LlmSettings) -> Any:
    """Create an OpenAI-compatible client for OCI Generative AI.

    Args:
        settings: LLM runtime settings.

    Returns:
        OpenAI-compatible client instance.
    """
    # pylint: disable=import-outside-toplevel
    from openai import OpenAI

    return OpenAI(
        base_url=settings.base_url,
        api_key=settings.api_key,
    )


def load_llm_settings(environ: Mapping[str, str] | None = None) -> LlmSettings:
    """Load LLM settings from environment variables.

    Args:
        environ: Optional environment mapping. Defaults to `os.environ` after
            loading local `.env` values.

    Returns:
        Parsed LLM runtime settings.

    Raises:
        ValueError: If the required API key is missing.
    """
    if environ is None:
        load_dotenv()
        source = os.environ
    else:
        source = environ

    model_id = source.get(AGENT_LLM_MODEL_ID_ENV, DEFAULT_LLM_MODEL_ID).strip()
    api_key = source.get(AGENT_LLM_API_KEY_ENV, "").strip()
    if not api_key:
        raise ValueError(f"{AGENT_LLM_API_KEY_ENV} is required")

    region = source.get(AGENT_LLM_OCI_REGION_ENV, DEFAULT_LLM_OCI_REGION).strip()
    base_url = source.get(AGENT_LLM_BASE_URL_ENV, "").strip()
    if not base_url:
        base_url = build_oci_openai_base_url(region)

    return LlmSettings(
        model_id=model_id or DEFAULT_LLM_MODEL_ID,
        api_key=api_key,
        base_url=base_url,
    )


def build_oci_openai_base_url(region: str) -> str:
    """Build the OCI OpenAI-compatible inference endpoint.

    Args:
        region: OCI region identifier.

    Returns:
        OpenAI-compatible OCI inference endpoint.

    Raises:
        ValueError: If `region` is empty.
    """
    cleaned_region = region.strip()
    if not cleaned_region:
        raise ValueError(f"{AGENT_LLM_OCI_REGION_ENV} must not be empty")

    return (
        f"https://inference.generativeai.{cleaned_region}."
        "oci.oraclecloud.com/openai/v1"
    )


def extract_response_text(response: Any) -> str:
    """Extract text from a Responses API response-like object.

    Args:
        response: OpenAI Responses API response object or compatible fake.

    Returns:
        Extracted model output text.

    Raises:
        ValueError: If no output text is available.
    """
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    for item in _iter_response_output(response):
        for content in _get_value(item, "content", []):
            text = _get_value(content, "text", None)
            if isinstance(text, str) and text.strip():
                return text

    raise ValueError("Responses API response did not contain output text")


def _iter_response_output(response: Any) -> list[Any]:
    """Return response output items from dict-like or SDK response objects."""
    output = _get_value(response, "output", [])
    return list(output or [])


def _get_value(value: Any, key: str, default: Any) -> Any:
    """Read a value from either a mapping or an SDK model-like object."""
    if isinstance(value, Mapping):
        return value.get(key, default)

    return getattr(value, key, default)
