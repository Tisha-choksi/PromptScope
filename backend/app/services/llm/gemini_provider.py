import os
import time
from typing import Optional

from tenacity import retry, stop_after_attempt, wait_exponential

from app.services.llm.base import BaseLLMProvider, LLMResponse

try:
    import google.generativeai as genai
    _gemini_available = True
except ImportError:
    _gemini_available = False


class GeminiProvider(BaseLLMProvider):
    provider_name = "gemini"
    default_model = "gemini-1.5-flash"

    def __init__(self, model: Optional[str] = None):
        self.model = model or self.default_model
        self._configured = False

    def _ensure_configured(self) -> None:
        if not self._configured:
            if not _gemini_available:
                raise ImportError("google-generativeai package is not installed")
            api_key = os.environ.get("GOOGLE_API_KEY")
            genai.configure(api_key=api_key)
            self._configured = True

    def is_available(self) -> bool:
        return _gemini_available and bool(os.environ.get("GOOGLE_API_KEY"))

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        model_name = kwargs.get("model", self.model)
        start = time.time()
        try:
            self._ensure_configured()
            gemini_model = genai.GenerativeModel(model_name)
            response = await gemini_model.generate_content_async(prompt)
            latency_ms = int((time.time() - start) * 1000)
            response_text = response.text if hasattr(response, "text") else ""
            # Gemini usage metadata may not always be present
            tokens_used: Optional[int] = None
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                meta = response.usage_metadata
                input_tokens = getattr(meta, "prompt_token_count", 0) or 0
                output_tokens = getattr(meta, "candidates_token_count", 0) or 0
                tokens_used = input_tokens + output_tokens
            return LLMResponse(
                provider=self.provider_name,
                model=model_name,
                prompt_text=prompt,
                response_text=response_text,
                tokens_used=tokens_used,
                latency_ms=latency_ms,
                success=True,
            )
        except Exception as e:
            latency_ms = int((time.time() - start) * 1000)
            return LLMResponse(
                provider=self.provider_name,
                model=model_name,
                prompt_text=prompt,
                response_text="",
                tokens_used=None,
                latency_ms=latency_ms,
                error=str(e),
                success=False,
            )
