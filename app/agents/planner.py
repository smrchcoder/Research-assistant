"""Planner agent for generating retrieval plans from user queries."""

import logging
from typing import Any, Dict, List, Optional

from tenacity import retry, retry_if_exception, stop_after_attempt, wait_fixed

from ..models import ConversationalHistoryModel, PlannerConfig
from .base import LLMAgent
from .prompts import PLANNER_PROMPT

logger = logging.getLogger(__name__)


class Planner(LLMAgent):
    """
    Agent responsible for analyzing user queries and generating retrieval plans.

    The planner resolves ambiguous references using conversation history,
    classifies question types, and determines optimal search strategies.
    """

    def __init__(
        self,
        config: Optional[PlannerConfig] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        llm_client_instance: Optional[Any] = None,
    ):
        """
        Initialize the Planner agent.

        Args:
            config: Configuration for the planner agent
            conversation_history: Previous conversation for context
            llm_client_instance: LLM client for API calls
        """
        super().__init__(
            system_prompt=PLANNER_PROMPT,
            llm_client=llm_client_instance,
            config=config,
        )
        self.conversation_history: List[ConversationalHistoryModel] = []

        if conversation_history:
            self._build_conversation_history(conversation_history)

    def _build_conversation_history(
        self, conversation_history: List[Dict[str, Any]]
    ) -> None:
        """
        Build validated conversation history from raw data.

        Args:
            conversation_history: List of conversation dictionaries
        """
        if not conversation_history:
            return

        # Take the most recent N records
        records_to_take = min(
            self.config.max_history_records, len(conversation_history)
        )
        recent_conversations = conversation_history[-records_to_take:]

        try:
            self.conversation_history = [
                ConversationalHistoryModel(**conversation)
                for conversation in recent_conversations
            ]
            logger.info(f"Loaded {len(self.conversation_history)} conversation records")
        except Exception as e:
            logger.error(f"Error extracting conversation history: {str(e)}")
            self.conversation_history = []

    def _build_user_prompt(self, query: str) -> str:
        """
        Build the user prompt including conversation history.

        Args:
            query: User's question

        Returns:
            Formatted user prompt string
        """
        user_prompt = f"Query: {query}"

        if self.conversation_history:
            conversation_summary = "\n\nPrevious Conversation:\n"
            for idx, conversation in enumerate(self.conversation_history, 1):
                conversation_summary += (
                    f"Q{idx}: {conversation.question}\n"
                    f"A{idx}: {conversation.answer}\n"
                )
            user_prompt += conversation_summary

        return user_prompt

    @retry(
        retry=retry_if_exception(lambda e: isinstance(e, ConnectionError)),
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
    )
    def plan_questions(self, query: str) -> Dict[str, Any]:
        """
        Generate a retrieval plan for the given query.

        Args:
            query: User's question

        Returns:
            Dictionary containing the retrieval plan

        Raises:
            ValueError: If query is empty or LLM returns invalid JSON
            ConnectionError: If LLM API call fails after retries
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        # Track reasoning: query analysis
        self.add_reasoning_step(
            "analysis",
            f"Analyzing query complexity and intent",
            {
                "query": query,
                "query_length": len(query),
                "has_history": len(self.conversation_history) > 0,
            },
        )

        user_prompt = self._build_user_prompt(query)
        messages = self._build_messages(user_prompt)
        raw_response = self._call_llm(messages)

        plan = self._validate_plan(raw_response, query)
        logger.info(f"Generated plan: {plan}")
        return plan

    def _validate_plan(self, raw_response: str, query: str) -> Dict[str, Any]:
        """
        Validate and parse the LLM response into a plan.

        Args:
            raw_response: Raw JSON response from LLM
            query: Original user query

        Returns:
            Validated plan dictionary

        Raises:
            ValueError: If response is not valid JSON or missing required fields
        """
        plan = self._parse_json_response(raw_response)

        # Validate required fields
        required_fields = ["resolved_question", "question_type", "search_queries"]
        missing_fields = [f for f in required_fields if f not in plan]

        if missing_fields:
            raise ValueError(f"Plan missing required fields: {missing_fields}")

        # Track reasoning: plan generation
        search_queries = plan.get("search_queries", [])
        self.add_reasoning_step(
            "planning",
            f"Generated {len(search_queries)} search strategies",
            {
                "num_queries": len(search_queries),
                "question_type": plan.get("question_type"),
                "strategies": [
                    q.get("rationale", "")
                    for q in search_queries
                    if isinstance(q, dict)
                ],
            },
        )
        # Why is strategies field required ,
        # are we mentioning the LLM to generate something like this,
        #  I dont this jsonwill agev rationale field:TODO

        logger.info(f"Generated plan with {len(search_queries)} search queries")
        return plan

    def execute(self, query: str) -> Dict[str, Any]:
        """
        Execute the planner agent.

        Args:
            query: User's question

        Returns:
            Generated retrieval plan with reasoning trace
        """
        plan = self.plan_questions(query)
        # Include reasoning trace in the plan
        plan["reasoning"] = self.get_reasoning_trace()
        return plan
