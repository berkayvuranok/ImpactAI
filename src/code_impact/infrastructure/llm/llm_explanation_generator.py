"""LLM-powered explanation generator with template fallback."""

from __future__ import annotations

import json
import re

from code_impact.domain.entities import PredictionExplanation
from code_impact.domain.services import ExplanationContext, IExplanationGenerator
from code_impact.infrastructure.config.logging import get_logger
from code_impact.infrastructure.llm.llm_client import ILLMClient
from code_impact.infrastructure.llm.prompt_builder import SYSTEM_PROMPT, build_explanation_prompt
from code_impact.infrastructure.llm.template_explanation_generator import TemplateExplanationGenerator

logger = get_logger(__name__)


class LLMExplanationGenerator(IExplanationGenerator):
    """Calls LLM to narrate pre-computed ML results. Falls back to template on error."""

    def __init__(
        self,
        llm_client: ILLMClient,
        fallback: IExplanationGenerator | None = None,
    ) -> None:
        self._llm = llm_client
        self._fallback = fallback or TemplateExplanationGenerator()

    async def generate(self, context: ExplanationContext) -> PredictionExplanation:
        user_prompt = build_explanation_prompt(context)
        try:
            raw = await self._llm.complete(SYSTEM_PROMPT, user_prompt)
            parsed = self._parse_response(raw)
            return PredictionExplanation(
                root_cause=parsed.get("root_cause", ""),
                risk_explanation=parsed.get("risk_explanation", ""),
                affected_files_explanation=parsed.get("affected_files_explanation", ""),
                reviewer_explanation=parsed.get("reviewer_explanation"),
                attention_summary={
                    "generator": "llm",
                    "fusion_metadata": context.fusion_metadata,
                    "similar_bug_count": len(context.similar_bugs),
                },
            )
        except Exception as exc:
            logger.warning("llm_explanation_fallback", error=str(exc))
            explanation = await self._fallback.generate(context)
            explanation.attention_summary["llm_fallback_reason"] = str(exc)
            return explanation

    @staticmethod
    def _parse_response(raw: str) -> dict[str, str]:
        text = raw.strip()
        fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if fence:
            text = fence.group(1).strip()
        data = json.loads(text)
        if not isinstance(data, dict):
            msg = "LLM response is not a JSON object"
            raise ValueError(msg)
        return {k: str(v) for k, v in data.items()}
