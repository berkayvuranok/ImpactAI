"""Factory for explanation generators based on settings."""

from __future__ import annotations

from code_impact.domain.services import IExplanationGenerator
from code_impact.infrastructure.config.settings import Settings
from code_impact.infrastructure.llm.llm_client import AnthropicLLMClient, OpenAILLMClient
from code_impact.infrastructure.llm.llm_explanation_generator import LLMExplanationGenerator
from code_impact.infrastructure.llm.template_explanation_generator import TemplateExplanationGenerator


def build_explanation_generator(settings: Settings) -> IExplanationGenerator:
    template = TemplateExplanationGenerator()

    if settings.llm_backend == "mock":
        return template

    if settings.llm_backend == "openai":
        if not settings.openai_api_key:
            return template
        client = OpenAILLMClient(
            api_key=settings.openai_api_key,
            model=settings.llm_model,
            max_tokens=settings.llm_max_tokens,
        )
        return LLMExplanationGenerator(client, fallback=template)

    if settings.llm_backend == "anthropic":
        if not settings.anthropic_api_key:
            return template
        client = AnthropicLLMClient(
            api_key=settings.anthropic_api_key,
            model=settings.llm_model,
            max_tokens=settings.llm_max_tokens,
        )
        return LLMExplanationGenerator(client, fallback=template)

    return template
