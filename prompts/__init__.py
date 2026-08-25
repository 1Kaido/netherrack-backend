# prompts/__init__.py

from .stone_model_prompt import STONE_PROMPT
from .iron_model_prompt import IRON_PROMPT
from .diamond_model_prompt import DIAMOND_PROMPT
from .netherite_model_prompt import NETHERITE_PROMPT

PROMPTS = {
    "stone": STONE_PROMPT,
    "iron": IRON_PROMPT,
    "diamond": DIAMOND_PROMPT,
    "netherite": NETHERITE_PROMPT,
}

MODELS = {
    "stone": "qwen/qwen3-8b",
    "iron": "qwen/qwen3-30b-a3b",
    "diamond": "qwen/qwen3-235b-a22b",
    "netherite": "openai/gpt-5.6-sol",
}