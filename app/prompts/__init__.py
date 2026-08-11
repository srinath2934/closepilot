"""Prompt Engineering Package for GWC AI Sales Agent."""
from app.prompts.strategy_prompts import (
    STRATEGY_SYSTEM_PROMPT,
    format_strategy_user_prompt
)
from app.prompts.communication_prompts import (
    COMMUNICATION_SYSTEM_PROMPT,
    format_communication_user_prompt
)

__all__ = [
    "STRATEGY_SYSTEM_PROMPT",
    "format_strategy_user_prompt",
    "COMMUNICATION_SYSTEM_PROMPT",
    "format_communication_user_prompt"
]
