from typing import Generator
from openai import OpenAI
from .base import LLMProvider


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o", temperature: float = 0.7, max_tokens: int = 4096):
        super().__init__(api_key, model, temperature, max_tokens)
        self.client = OpenAI(api_key=api_key)

    def chat(self, messages: list[dict], stream: bool = True) -> Generator[str, None, None]:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=stream,
        )
        if stream:
            for chunk in response:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta and delta.content:
                    yield delta.content
        else:
            yield response.choices[0].message.content or ""
