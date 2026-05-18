from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMResponse:
    provider: str
    model: str
    prompt_text: str
    response_text: str
    tokens_used: Optional[int]
    latency_ms: int
    error: Optional[str] = None
    success: bool = True


class BaseLLMProvider(ABC):
    provider_name: str
    default_model: str

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> LLMResponse: ...

    @abstractmethod
    def is_available(self) -> bool: ...
