from typing import Generator
from anthropic import Anthropic
from .base import LLMProvider


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514", temperature: float = 0.7, max_tokens: int = 4096):
        super().__init__(api_key, model, temperature, max_tokens)
        self.client = Anthropic(api_key=api_key)

    def chat(self, messages: list[dict], stream: bool = True) -> Generator[str, None, None]:
        system = ""
        filtered = []
        for m in messages:
            if m["role"] == "system":
                system = m["content"]
            else:
                filtered.append(m)

        with self.client.messages.stream(
            model=self.model,
            system=system or None,
            messages=filtered,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        ) as stream:
            for text in stream.text_stream:
                yield text
