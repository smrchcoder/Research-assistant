"""
Agents module for multi-agent document retrieval and synthesis.

This module provides specialized agents for:
- Planning: Query analysis and retrieval strategy
- Retrieval: Document similarity search
- Evaluation: Context sufficiency assessment  
- Synthesis: Final answer generation
- Refinement: Iterative improvement control
"""

from .base import Agent, LLMAgent
from .evaluator import Evaluator
from .planner import Planner
from .prompts import EVALUATION_PROMPT, PLANNER_PROMPT, SYNTHESIZER_PROMPT
from .retriver import Retriever
from .synthesizer import Synthesizer
from .refinement_controller import RefinementController

__all__ = [
    # Base classes
    "Agent",
    "LLMAgent",
    # Agent implementations
    "Planner",
    "Retriever",
    "Evaluator",
    "Synthesizer",
    "RefinementController",
    # Prompts
    "PLANNER_PROMPT",
    "EVALUATION_PROMPT",
    "SYNTHESIZER_PROMPT",
]