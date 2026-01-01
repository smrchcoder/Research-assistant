"""Retriever agent for document retrieval operations."""

import logging
from typing import Any, List

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

    def retrieve_documents(self, query: str, top_k: int = 5) -> List[Any]:
        """
        Retrieve documents similar to the given query.

        Args:
            query: Search query string
            top_k: Number of top results to return

        Returns:
            List of retrieved documents

        Raises:
            ValueError: If query is empty
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        query_service = QueryService(query=query)
        documents = query_service.retrieve_similarities(top_k=top_k)
        
        logger.info(f"Retrieved {len(documents)} documents for query: {query[:50]}...")
        return documents

    def execute(self, query: str, top_k: int = 5) -> List[Any]:
        """
        Execute the retriever agent.

        Args:
            query: Search query string
            top_k: Number of top results to return

        Returns:
            List of retrieved documents
        """
        return self.retrieve_documents(query=query, top_k=top_k)