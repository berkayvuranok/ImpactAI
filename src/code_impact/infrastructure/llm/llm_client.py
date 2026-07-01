"""LLM client protocol and provider implementations."""

from __future__ import annotations

from typing import Protocol


class ILLMClient(Protocol):
    async def complete(self, system_prompt: str, user_prompt: str) -> str: ...


class OpenAILLMClient:
    def __init__(self, api_key: str, model: str, max_tokens: int = 2048) -> None:
        self._api_key = api_key
        self._model = model
        self._max_tokens = max_tokens

    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self._api_key)
        response = await client.chat.completions.create(
            model=self._model,
            max_tokens=self._max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        content = response.choices[0].message.content
        return content or ""


class AnthropicLLMClient:
    def __init__(self, api_key: str, model: str, max_tokens: int = 2048) -> None:
        self._api_key = api_key
        self._model = model
        self._max_tokens = max_tokens

    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=self._api_key)
        response = await client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=0.2,
        )
        parts = [block.text for block in response.content if block.type == "text"]
        return "".join(parts)
