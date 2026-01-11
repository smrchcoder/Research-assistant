"""Synthesizer agent for generating final answers from retrieved context."""

import logging
from typing import Any, Dict, List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

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

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(ConnectionError),
        reraise=True
    )
    def generate_answer(self, context: str, query: str, metadatas: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate an answer using the LLM based on context and query.

        Args:
            context: Formatted context from retrieved documents
            query: User's question
            metadatas: List of metadata for source citations

        Returns:
            Dictionary with answer and citations

        Raises:
            ConnectionError: If LLM API call fails
        """
        messages = self._generate_context_prompt(context, query)
        answer = self._call_llm(messages)
        
        # Extract citations from metadata
        citations = []
        if metadatas:
            seen_sources = set()
            for meta in metadatas:
                source_key = (
                    meta.get('document_id', 'Unknown'),
                    meta.get('page_number', 'Unknown')
                )
                if source_key not in seen_sources:
                    citations.append({
                        'document_id': meta.get('document_id', 'Unknown'),
                        'page_number': meta.get('page_number', 'Unknown'),
                        'chunk_id': meta.get('chunk_id', 'Unknown')
                    })
                    seen_sources.add(source_key)
        
        logger.info(f"Generated answer with {len(citations)} citations for query: {query[:50]}...")
        return {
            'answer': answer,
            'citations': citations
        }

    def execute(
        self,
        context: str,
        query: str,
        session_id: str,
        session_store: SessionStore,
        metadatas: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute the synthesizer agent.

        Args:
            context: Formatted context from retrieved documents
            query: User's question
            session_id: Session identifier for storing conversation
            session_store: Session storage instance
            metadatas: List of metadata for source citations

        Returns:
            Dictionary containing the answer, citations, session update status, and reasoning trace
        """
        # Track reasoning: start synthesis
        self.add_reasoning_step(
            "synthesis_start",
            "Beginning answer generation from context",
            {"context_length": len(context), "query": query[:100]}
        )
        
        result = self.generate_answer(context=context, query=query, metadatas=metadatas)
        answer = result['answer']
        citations = result['citations']
        
        # Track reasoning: answer generated
        self.add_reasoning_step(
            "answer_generated",
            f"Generated answer of {len(answer)} characters with {len(citations)} citations",
            {"answer_length": len(answer), "citations_count": len(citations)}
        )
        
        results: Dict[str, Any] = {
            "answer": answer,
            "citations": citations
        }
        
        try:
            session_store.add_message(
                session_id=session_id,
                answer=answer,
                question=query
            )
            results["session_updated"] = True
            self.add_reasoning_step(
                "session_update",
                "Successfully updated conversation history",
                {"session_id": session_id}
            )
        except Exception as e:
            logger.error(f"Failed to update session: {str(e)}")
            results["session_updated"] = False
            self.add_reasoning_step(
                "session_update_error",
                "Failed to update conversation history",
                {"error": str(e)}
            )
        
        # Add reasoning trace to results
        results["reasoning"] = self.get_reasoning_trace()
        return results
