"""
Author: L. Saetta
Date last modified: 2026-07-07
License: MIT
Description: Unit tests for sample agent LLM client helpers.
Agent customization: Update when the sample agent LLM integration changes.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from oci_langgraph_a2a_blueprint.agent.llm_client import (
    DEFAULT_LLM_MODEL_ID,
    LlmSettings,
    ResponsesApiLlmClient,
    build_oci_openai_base_url,
    extract_response_text,
    load_llm_settings,
)


class FakeResponsesResource:
    """Fake Responses API resource that records the request."""

    def __init__(self) -> None:
        self.request: dict | None = None

    def create(self, **kwargs: object) -> SimpleNamespace:
        """Record kwargs and return a response-like object."""
        self.request = dict(kwargs)
        return SimpleNamespace(output_text="fake llm answer")


class FakeOpenAIClient:
    """Fake OpenAI-compatible client for unit tests."""

    def __init__(self) -> None:
        self.responses = FakeResponsesResource()


def test_load_llm_settings_defaults_and_derives_oci_base_url() -> None:
    """Verify required and default LLM settings."""
    settings = load_llm_settings({"AGENT_LLM_API_KEY": "secret"})

    assert settings == LlmSettings(
        model_id=DEFAULT_LLM_MODEL_ID,
        api_key="secret",
        base_url=(
            "https://inference.generativeai.us-chicago-1."
            "oci.oraclecloud.com/openai/v1"
        ),
    )


def test_load_llm_settings_accepts_overrides() -> None:
    """Verify explicit model id, region, and base URL overrides."""
    settings = load_llm_settings(
        {
            "AGENT_LLM_MODEL_ID": "openai.custom",
            "AGENT_LLM_API_KEY": "secret",
            "AGENT_LLM_OCI_REGION": "eu-frankfurt-1",
            "AGENT_LLM_BASE_URL": "https://example.com/openai/v1",
        }
    )

    assert settings.model_id == "openai.custom"
    assert settings.api_key == "secret"
    assert settings.base_url == "https://example.com/openai/v1"


def test_load_llm_settings_requires_api_key() -> None:
    """Verify missing API key fails before creating a real client."""
    with pytest.raises(ValueError, match="AGENT_LLM_API_KEY is required"):
        load_llm_settings({})


def test_build_oci_openai_base_url_rejects_empty_region() -> None:
    """Verify invalid region values fail clearly."""
    with pytest.raises(ValueError, match="AGENT_LLM_OCI_REGION must not be empty"):
        build_oci_openai_base_url(" ")


def test_responses_api_llm_client_calls_model_with_original_input() -> None:
    """Verify the LLM client uses Responses API with model and input text."""
    fake_client = FakeOpenAIClient()
    llm_client = ResponsesApiLlmClient(
        client=fake_client,
        model_id="openai.gpt-5.5",
    )

    answer = llm_client.answer("hello")

    assert answer == "fake llm answer"
    assert fake_client.responses.request == {
        "model": "openai.gpt-5.5",
        "input": "hello",
    }


def test_extract_response_text_reads_output_text() -> None:
    """Verify standard `output_text` extraction."""
    response = SimpleNamespace(output_text="direct text")

    assert extract_response_text(response) == "direct text"


def test_extract_response_text_reads_output_content_fallback() -> None:
    """Verify fallback extraction from response output content."""
    response = {
        "output": [
            {
                "content": [
                    {
                        "text": "fallback text",
                    }
                ]
            }
        ]
    }

    assert extract_response_text(response) == "fallback text"


def test_extract_response_text_rejects_missing_text() -> None:
    """Verify empty model responses fail clearly."""
    with pytest.raises(
        ValueError,
        match="Responses API response did not contain output text",
    ):
        extract_response_text(SimpleNamespace(output=[]))
