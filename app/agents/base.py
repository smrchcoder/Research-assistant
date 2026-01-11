"""Base agent module providing common functionality for all agents."""

import json
import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from ..models import PlannerConfig

logger = logging.getLogger(__name__)


class Agent(ABC):
    """Base class for all agents in the system."""

    def __init__(
        self,
        system_prompt: str,
        llm_client: Optional[Any] = None,
        config: Optional[PlannerConfig] = None,
        tools: Optional[Dict[str, Callable]] = None,
        reasoning_steps: Optional[List[Dict[str, Any]]] = None,
    ):
        self.agent_id: str = str(uuid.uuid4())
        self.system_prompt: str = system_prompt
        self.llm_client: Optional[Any] = llm_client
        self.config: PlannerConfig = config or PlannerConfig()
        self.tools: Dict[str, Callable] = tools or {}
        self.reasoning_steps: List[Dict[str, Any]] = reasoning_steps or []

    def describe(self) -> Dict[str, Any]:
        """Get a description of this agent."""
        return {
            "agent_id": self.agent_id,
            "tools_available": list(self.tools.keys()),
            "reasoning_steps_count": len(self.reasoning_steps),
            "system_prompt": self.system_prompt,
        }

    def add_reasoning_step(
        self, step_type: str, description: str, data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a reasoning step to the agent's history with timestamp.

        Args:
            step_type: Type of reasoning step (e.g., 'analysis', 'planning', 'evaluation')
            description: Human-readable description of what happened
            data: Optional additional structured data about the step
        """
        reasoning_entry = {
            "agent": self.__class__.__name__,
            "step_type": step_type,
            "description": description,
            "timestamp": datetime.time().isoformat(),
            "data": data or {},
        }
        self.reasoning_steps.append(reasoning_entry)
        logger.debug(
            f"{self.__class__.__name__} reasoning: {step_type} - {description}"
        )

    def get_reasoning_trace(self) -> List[Dict[str, Any]]:
        """Return complete reasoning trace for this agent.

        Returns:
            List of reasoning steps with timestamps and context
        """
        return self.reasoning_steps.copy()

    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """Execute the agent's main task. Must be implemented by subclasses."""
        pass


class LLMAgent(Agent):
    """
    Base class for agents that interact with LLM.

    Provides common LLM calling, prompt generation, and JSON parsing utilities.
    """

    def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        """
        Call the LLM with the given messages.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys

        Returns:
            LLM response content

        Raises:
            ConnectionError: If LLM API call fails
            ValueError: If llm_client is not configured
        """
        if not self.llm_client:
            raise ValueError("LLM client is not configured")

        try:
            response = self.llm_client.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM API call failed: {str(e)}")
            raise ConnectionError(f"Failed to call LLM: {str(e)}")

    def _build_messages(
        self, user_prompt: str, system_prompt: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Build message list for LLM API call.

        Args:
            user_prompt: The user's prompt/query
            system_prompt: Optional system prompt override

        Returns:
            List of message dictionaries for OpenAI API
        """
        return [
            {"role": "system", "content": system_prompt or self.system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _generate_context_prompt(
        self, context: str, query: str
    ) -> List[Dict[str, str]]:
        """
        Generate prompt messages with context and query.

        Args:
            context: Formatted context from retrieved documents
            query: User's question

        Returns:
            List of message dictionaries for OpenAI API
        """
        user_prompt = f"""
        Context:
        {context}
        ---
        Question: {query}
        """

        logger.debug(f"Generated prompt for query: {query[:50]}...")
        return self._build_messages(user_prompt)

    @staticmethod
    def _parse_json_response(raw_response: str) -> Dict[str, Any]:
        """
        Parse and clean JSON response from LLM.

        Args:
            raw_response: Raw response string from LLM

        Returns:
            Parsed JSON as dictionary

        Raises:
            ValueError: If response cannot be parsed as valid JSON
        """
        cleaned_response = raw_response.strip()

        # Handle markdown code blocks
        if cleaned_response.startswith("```"):
            parts = cleaned_response.split("```")
            if len(parts) >= 2:
                cleaned_response = parts[1]
                if cleaned_response.startswith("json"):
                    cleaned_response = cleaned_response[4:]
                cleaned_response = cleaned_response.strip()

        try:
            return json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {raw_response}")
            raise ValueError(f"Invalid JSON response: {str(e)}")
