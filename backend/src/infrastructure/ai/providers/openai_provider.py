"""OpenAI LLM Provider implementation."""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, List

from .base_provider import AIProvider


class OpenAIProvider(AIProvider):
    """OpenAI API client for chat completions."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self._api_key = api_key
        self._base_url = base_url

    async def chat(self, messages: List[Dict[str, str]], model_config: Any) -> str:
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=self._api_key, base_url=self._base_url)
            kwargs = {
                "model": model_config.model_name,
                "messages": messages,
                "temperature": model_config.temperature,
                "max_tokens": model_config.max_tokens,
            }
            if model_config.top_p != 1.0:
                kwargs["top_p"] = model_config.top_p
            if model_config.stop_sequences:
                kwargs["stop"] = list(model_config.stop_sequences)

            response = await client.chat.completions.create(**kwargs)
            return response.choices[0].message.content or ""
        except ImportError:
            raise RuntimeError("openai package not installed. Install with: pip install openai")
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {e}")

    async def chat_stream(self, messages: List[Dict[str, str]], model_config: Any) -> AsyncIterator[str]:
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=self._api_key, base_url=self._base_url)
            stream = await client.chat.completions.create(
                model=model_config.model_name,
                messages=messages,
                temperature=model_config.temperature,
                max_tokens=model_config.max_tokens,
                stream=True,
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except ImportError:
            raise RuntimeError("openai package not installed")
        except Exception as e:
            raise RuntimeError(f"OpenAI streaming error: {e}")