from typing import Generator
from google import genai
from .base import LLMProvider


class GoogleProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash", temperature: float = 0.7, max_tokens: int = 4096):
        super().__init__(api_key, model, temperature, max_tokens)
        self.client = genai.Client(api_key=api_key)

    def chat(self, messages: list[dict], stream: bool = True) -> Generator[str, None, None]:
        history = []
        system = ""
        for m in messages:
            if m["role"] == "system":
                system = m["content"]
            elif m["role"] == "user":
                history.append({"role": "user", "parts": [m["content"]]})
            elif m["role"] == "assistant":
                history.append({"role": "model", "parts": [m["content"]]})

        contents = history if not system else history
        config = {
            "temperature": self.temperature,
            "max_output_tokens": self.max_tokens,
        }

        response = self.client.models.generate_content_stream(
            model=self.model,
            contents=contents,
            config=config,
        )
        for chunk in response:
            if chunk.text:
                yield chunk.text
