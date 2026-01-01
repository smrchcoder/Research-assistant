"""Synthesizer agent for generating final answers from retrieved context."""

import logging
from typing import Any, Dict, List, Optional

from ..memory import SessionStore
from ..models import PlannerConfig
from .base import LLMAgent
from .prompts import SYNTHESIZER_PROMPT

logger = logging.getLogger(__name__)


class Synthesizer(LLMAgent):
    """
    Agent responsible for synthesizing final answers from retrieved context.
    
    Generates clear, well-structured answers based on provided document context
    while maintaining proper citations and avoiding speculation.
    """

    def __init__(
        self, 
        llm_client: Optional[Any] = None,
        config: Optional[PlannerConfig] = None
    ):
        """
        Initialize the Synthesizer agent.

        Args:
            llm_client: LLM client for API calls
            config: Configuration for the synthesizer agent
        """
        super().__init__(
            system_prompt=SYNTHESIZER_PROMPT,
            llm_client=llm_client,
            config=config,
        )

    def generate_answer(self, context: str, query: str) -> str:
        """
        Generate an answer using the LLM based on context and query.

        Args:
            context: Formatted context from retrieved documents
            query: User's question

        Returns:
            Generated answer text

        Raises:
            ConnectionError: If LLM API call fails
        """
        messages = self._generate_context_prompt(context, query)
        answer = self._call_llm(messages)
        
        logger.info(f"Generated answer for query: {query[:50]}...")
        return answer

    def execute(
        self,
        context: str,
        query: str,
        session_id: str,
        session_store: SessionStore
    ) -> Dict[str, Any]:
        """
        Execute the synthesizer agent.

        Args:
            context: Formatted context from retrieved documents
            query: User's question
            session_id: Session identifier for storing conversation
            session_store: Session storage instance

        Returns:
            Dictionary containing the answer and session update status
        """
        answer = self.generate_answer(context=context, query=query)
        
        results: Dict[str, Any] = {"answer": answer}
        
        try:
            session_store.add_message(
                session_id=session_id,
                answer=answer,
                question=query
            )
            results["session_updated"] = True
        except Exception as e:
            logger.error(f"Failed to update session: {str(e)}")
            results["session_updated"] = False

        return results
