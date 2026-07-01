"""Tests for LLM explanation JSON parsing."""

import pytest

from code_impact.infrastructure.llm.llm_explanation_generator import LLMExplanationGenerator


class FakeLLM:
    def __init__(self, response: str) -> None:
        self._response = response

    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        return self._response


@pytest.mark.asyncio
async def test_llm_generator_parses_json():
    raw = """{"root_cause": "Complex refactor", "risk_explanation": "High churn", """
    raw += """"affected_files_explanation": "Parser module", "reviewer_explanation": "Alice owns it"}"""
    gen = LLMExplanationGenerator(FakeLLM(raw))
    parsed = gen._parse_response(raw)
    assert parsed["root_cause"] == "Complex refactor"


@pytest.mark.asyncio
async def test_llm_generator_parses_fenced_json():
    raw = '```json\n{"root_cause": "Bug fix", "risk_explanation": "Low", '
    raw += '"affected_files_explanation": "One file", "reviewer_explanation": "Bob"}\n```'
    gen = LLMExplanationGenerator(FakeLLM(raw))
    parsed = gen._parse_response(raw)
    assert parsed["root_cause"] == "Bug fix"
