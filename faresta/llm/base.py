from abc import ABC, abstractmethod
from typing import Generator


class LLMProvider(ABC):
    def __init__(self, api_key: str, model: str, temperature: float = 0.7, max_tokens: int = 4096):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    @abstractmethod
    def chat(self, messages: list[dict], stream: bool = True) -> Generator[str, None, None]:
        ...
