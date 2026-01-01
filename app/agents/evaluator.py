"""Evaluator agent for assessing retrieval quality and context sufficiency."""

import logging
from typing import Any, Dict, List, Optional

from tenacity import retry, retry_if_exception, wait_fixed

from ..models import EvaluationResult, PlannerConfig
from .base import LLMAgent
from .prompts import EVALUATION_PROMPT

logger = logging.getLogger(__name__)


class Evaluator(LLMAgent):
    """
    Agent responsible for evaluating whether retrieved context is sufficient.

    Assesses coverage, depth, and confidence to determine if the retrieved
    information can adequately answer the user's question.
    """

    def __init__(
        self,
        llm_client_instance: Optional[Any] = None,
        config: Optional[PlannerConfig] = None,
    ):
        """
        Initialize the Evaluator agent.

        Args:
            llm_client_instance: LLM client for API calls
            config: Configuration for the evaluator agent
        """
        super().__init__(
            system_prompt=EVALUATION_PROMPT,
            llm_client=llm_client_instance,
            config=config,
        )

    @retry(
        retry=retry_if_exception(lambda e: isinstance(e, ConnectionError)),
        wait=wait_fixed(2),
    )
    def evaluate_context(self, context: str, query: str) -> EvaluationResult:
        """
        Evaluate whether the retrieved context is sufficient to answer the query.

        Args:
            context: Formatted context from retrieved documents
            query: User's question

        Returns:
            EvaluationResult containing assessment details

        Raises:
            ConnectionError: If LLM API call fails
            ValueError: If evaluation response cannot be parsed
        """
        messages = self._generate_context_prompt(context, query)
        raw_response = self._call_llm(messages)

        logger.debug(f"Evaluation response: {raw_response}")

        evaluation_data = self._parse_json_response(raw_response)

        return EvaluationResult(
            confidence_score=evaluation_data.get("confidence_score", 0.0),
            is_sufficient=evaluation_data.get("is_sufficient", False),
            suggested_followups=evaluation_data.get("suggested_followups", []),
            missing_aspects=evaluation_data.get("missing_aspects", []),
        )

    def execute(self, context: str, query: str) -> EvaluationResult:
        """
        Execute the evaluator agent.

        Args:
            context: Formatted context from retrieved documents
            query: User's question

        Returns:
            EvaluationResult with assessment details
        """
        return self.evaluate_context(context=context, query=query)
