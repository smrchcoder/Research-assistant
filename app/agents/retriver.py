"""Retriever agent for document retrieval operations."""

import logging
from typing import Any, List
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..services import QueryService
from .base import Agent

logger = logging.getLogger(__name__)


class Retriever(Agent):
    """
    Agent responsible for retrieving relevant documents from the vector store.
    
    Uses similarity search to find documents most relevant to the query.
    """

    def __init__(self):
        """Initialize the Retriever agent."""
        super().__init__(system_prompt="")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True
    )
    def retrieve_documents(self, query: str, top_k: int = 5, document_filenames: List[str] = None) -> List[Any]:
        """
        Retrieve documents similar to the given query.

        Args:
            query: Search query string
            top_k: Number of top results to return
            document_filenames: Optional list of document filenames to filter by

        Returns:
            List of retrieved documents

        Raises:
            ValueError: If query is empty
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        query_service = QueryService(query=query)
        documents = query_service.retrieve_similarities(top_k=top_k, document_filenames=document_filenames)
        
        logger.info(f"Retrieved {len(documents)} documents for query: {query[:50]}...")
        return documents

    def execute(self, query: str, top_k: int = 5, document_filenames: List[str] = None) -> List[Any]:
        """
        Execute the retriever agent.

        Args:
            query: Search query string
            top_k: Number of top results to return
            document_filenames: Optional list of document filenames to filter by

        Returns:
            List of retrieved documents
        """
        return self.retrieve_documents(query=query, top_k=top_k, document_filenames=document_filenames)