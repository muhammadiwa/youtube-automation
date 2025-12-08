"""OpenAI API client wrapper.

Provides a configured OpenAI client for AI content generation.
Requirements: 14.1, 14.2, 14.3
"""

import json
from typing import Optional, Any

from openai import AsyncOpenAI

from app.core.config import settings


class OpenAIClientError(Exception):
    """Base exception for OpenAI client errors."""
    pass


class OpenAIClient:
    """Wrapper for OpenAI API client."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize OpenAI client.

        Args:
            api_key: OpenAI API key. Uses settings if not provided.
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.temperature = settings.OPENAI_TEMPERATURE

        if not self.api_key:
            raise OpenAIClientError("OpenAI API key not configured")

        self._client = AsyncOpenAI(api_key=self.api_key)

    async def generate_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[dict] = None,
    ) -> str:
        """Generate a completion using OpenAI API.

        Args:
            system_prompt: System message for context
            user_prompt: User message/query
            temperature: Override default temperature
            max_tokens: Override default max tokens
            response_format: Optional response format (e.g., {"type": "json_object"})

        Returns:
            str: Generated completion text

        Raises:
            OpenAIClientError: If API call fails
        """
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

            kwargs: dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature or self.temperature,
                "max_tokens": max_tokens or self.max_tokens,
            }

            if response_format:
                kwargs["response_format"] = response_format

            response = await self._client.chat.completions.create(**kwargs)

            if not response.choices:
                raise OpenAIClientError("No response generated")

            return response.choices[0].message.content or ""

        except Exception as e:
            raise OpenAIClientError(f"OpenAI API error: {str(e)}") from e

    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> dict:
        """Generate a JSON response using OpenAI API.

        Args:
            system_prompt: System message for context
            user_prompt: User message/query
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Returns:
            dict: Parsed JSON response

        Raises:
            OpenAIClientError: If API call fails or JSON parsing fails
        """
        response = await self.generate_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )

        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            raise OpenAIClientError(f"Failed to parse JSON response: {str(e)}") from e


# Singleton instance
_client: Optional[OpenAIClient] = None


def get_openai_client() -> OpenAIClient:
    """Get or create OpenAI client singleton.

    Returns:
        OpenAIClient: Configured OpenAI client
    """
    global _client
    if _client is None:
        _client = OpenAIClient()
    return _client
