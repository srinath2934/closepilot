"""Unified LLM Provider Interface supporting NVIDIA NIM, Groq, OpenAI, and Mock."""
import json
import logging
from typing import List, Dict, Any, Optional
from app.config.settings import settings

logger = logging.getLogger("sales_copilot.llm")


from langsmith import traceable


class BaseLLMProvider:
    """Base interface for LLM calls."""
    async def generate_response(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        raise NotImplementedError

    async def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        """Convenience alias for generate_response."""
        return await self.generate_response(system_prompt, user_prompt, temperature)
    
    @traceable(name="llm_generate_json")
    async def generate_json(self, system_prompt: str, user_prompt: str, temperature: float = 0.1) -> Dict[str, Any]:
        raw = await self.generate_response(system_prompt, user_prompt, temperature)
        import re
        clean = raw.strip()
        # Find JSON object block
        json_match = re.search(r"(\{.*\})", clean, re.DOTALL)
        if json_match:
            clean = json_match.group(1)
        if clean.startswith("```json"):
            clean = clean[7:]
        if clean.startswith("```"):
            clean = clean[3:]
        if clean.endswith("```"):
            clean = clean[:-3]
        try:
            return json.loads(clean.strip(), strict=False)
        except Exception:
            # Fallback to standard json loads
            return json.loads(clean.strip())


import httpx


class NIMAndGroqProvider(BaseLLMProvider):
    """Direct, high-performance async client for NVIDIA NIM, Groq, and OpenAI APIs."""
    def __init__(self, api_key: str, base_url: Optional[str] = None, model: str = "meta/llama-3.1-8b-instruct"):
        self.api_key = api_key
        self.base_url = (base_url or "https://integrate.api.nvidia.com/v1").rstrip("/")
        self.model = model
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    async def generate_response(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "max_tokens": 512
        }
        url = f"{self.base_url}/chat/completions"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, headers=self.headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Error calling LLM provider ({self.model} at {self.base_url}): {e}")
            raise e

    async def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        """Convenience alias for generate_response."""
        return await self.generate_response(system_prompt, user_prompt, temperature)


# Backward compatibility alias
OpenAILikeProvider = NIMAndGroqProvider


class MockLLMProvider(BaseLLMProvider):
    """High-fidelity Mock Provider for zero-cost offline testing and instant demonstration."""
    async def generate_response(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        if "strategy" in system_prompt.lower() or "strategy" in user_prompt.lower():
            return json.dumps({
                "summary": "Customer requested proposal customization 5 days ago. No follow-up logged since contract was dispatched.",
                "recommended_action": "SEND_FOLLOWUP_EMAIL",
                "rationale": "High deal value ($45,000) at 'Decision Maker Bought-In' stage. Timely nudges on custom SLA terms typically accelerate close rates."
            })
        elif "communication" in system_prompt.lower() or "draft" in user_prompt.lower():
            return json.dumps({
                "subject": "Follow-up regarding Enterprise Data Pipeline Proposal — Next Steps",
                "body": (
                    "Hi Sarah,\n\n"
                    "I wanted to follow up on the customized SLA and pricing structure we shared last Thursday. "
                    "We've incorporated the specific multi-region redundancy requirements your team highlighted during our technical review.\n\n"
                    "Do you have 10 minutes tomorrow afternoon to discuss any feedback or finalize the contract timeline?\n\n"
                    "Best regards,\nAlex Mercer\nSenior Enterprise Account Executive"
                ),
                "action_type": "CREATE_CRM_TASK_AND_DRAFT_EMAIL"
            })
        elif "intent" in system_prompt.lower() or "intent" in user_prompt.lower():
            return json.dumps({
                "intent": "FIND_FOLLOWUPS",
                "target_scope": "all_deals",
                "urgency": "high"
            })
        return "I have analyzed the sales context and prepared the grounded recommendation."

    async def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        return await self.generate_response(system_prompt, user_prompt, temperature)


def get_llm_provider() -> BaseLLMProvider:
    """Factory to return the configured LLM provider (NVIDIA NIM, Groq, or Mock)."""
    from app.config.settings import get_settings
    current_settings = get_settings()
    provider_name = current_settings.LLM_PROVIDER.lower()
    
    if provider_name == "nvidia" and current_settings.NVIDIA_API_KEY:
        return NIMAndGroqProvider(
            api_key=current_settings.NVIDIA_API_KEY,
            base_url=current_settings.NVIDIA_BASE_URL,
            model=current_settings.LLM_MODEL
        )
    elif provider_name == "groq" and current_settings.GROQ_API_KEY:
        return NIMAndGroqProvider(
            api_key=current_settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
            model="llama-3.3-70b-versatile"
        )
    elif provider_name == "openai" and current_settings.OPENAI_API_KEY:
        return NIMAndGroqProvider(
            api_key=current_settings.OPENAI_API_KEY,
            model="gpt-4o"
        )
    else:
        logger.info(f"Using MockLLMProvider (LLM_PROVIDER={provider_name})")
        return MockLLMProvider()
