"""
Chat service layer for handling chat-related business logic.
"""

from typing import Dict, Any, List, Optional
import logging
from ..agents import Planner, Retriever, Evaluator, Synthesizer
from ..memory.session_store import session_store
from ..models import PlannerConfig
from ..services import QueryPromptTemplate

logger = logging.getLogger(__name__)


class ChatService:
    """
    Service layer for chat operations.
    Handles business logic for query processing, planning, and retrieval.
    """

    def __init__(
        self,
        llm_client_instance=None,
        planner_config: Optional[PlannerConfig] = None,
        session_store=None,
    ):
        """
        Initialize chat service.

        Args:
            llm_client_instance: LLM client to use (optional, uses default if None)
            planner_config: Configuration for planner agent
        """
        self.llm_client = llm_client_instance
        self.planner_config = planner_config
        self.prompt_template = QueryPromptTemplate()
        self.evaluator = Evaluator(llm_client_instance=self.llm_client)
        self.synthesizer = Synthesizer(llm_client=self.llm_client)
        self.session_store = session_store

    def process_query(self, session_id: str, query: str) -> Dict[str, Any]:
        """
        Process a user query: validate session, plan retrieval, and execute.

        Args:
            session_id: User's session ID
            query: User's question

        Returns:
            Dictionary containing plan and retrieved documents

        Raises:
            ValueError: If session is invalid or query is empty
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        if not session_id or not session_id.strip():
            raise ValueError("Session ID cannot be empty")

        # Validate session and get history
        session_data = session_store.get_session(session_id)
        if not session_data:
            raise ValueError("Invalid session or session expired")

        conversation_history = session_data.get("conversations", [])

        # Generate retrieval plan
        plan = self._generate_plan(query, conversation_history)

        # Retrieve documents based on plan
        all_documents, all_metadata = self._retrieve_documents(plan)
        generated_context = self.prompt_template.generate_context(
            documents=all_documents, metadatas=all_metadata
        )
        evaluation = self.evaluator.execute(context=generated_context, query=query)
        response = {}
        if evaluation.is_sufficient:
            response = self.synthesizer.execute(
                context=generated_context,
                session_store=self.session_store,
                session_id=session_id,
                query=query,
            )

        return {
            "plan": plan,
            "documents": all_documents,
            "query": query,
            "session_id": session_id,
            "evaluation": evaluation,
            "response": response,
        }

    def _generate_plan(
        self, query: str, conversation_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate a retrieval plan using the Planner agent.

        Args:
            query: User's question
            conversation_history: Previous conversation turns

        Returns:
            Retrieval plan dictionary
        """
        planner = Planner(
            conversation_history=conversation_history,
            config=self.planner_config,
            llm_client_instance=self.llm_client,
        )

        plan = planner.execute(query)
        logger.info(
            f"Generated plan with {len(plan.get('search_queries', []))} queries"
        )

        return plan

    def _retrieve_documents(self, plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Retrieve documents based on the plan's search queries.

        Args:
            plan: Retrieval plan containing search queries

        Returns:
            Tuple of (unique documents list, corresponding metadata list)
        """

        retriever = Retriever()
        all_documents = []
        all_metadata = []
        all_ids = []

        search_queries = plan.get("search_queries", [])
        max_searches = plan.get("max_searches", 1)

        for idx, search_query in enumerate(search_queries[:max_searches]):
            try:
                # Handle both dict and tuple formats
                if isinstance(search_query, dict):
                    query = search_query.get("query", "")
                    top_k = search_query.get("top_k", 5)
                else:
                    query, top_k = search_query

                if not query:
                    logger.warning(f"Empty query at index {idx}, skipping")
                    continue

                search_results = retriever.execute(query=query, top_k=top_k)

                # Extract all result components
                ids = search_results.get("ids", [[]])[0]
                documents = search_results.get("documents", [[]])[0]
                metadatas = search_results.get("metadatas", [[]])[0]

                all_ids.extend(ids or [])
                all_documents.extend(documents or [])
                all_metadata.extend(metadatas or [])

                logger.info(
                    f"Retrieved {len(documents or [])} documents for query: {query}"
                )

            except Exception as e:
                logger.error(f"Error retrieving documents for query {idx}: {str(e)}")
                continue

        # Remove duplicates using IDs (more efficient and accurate)
        seen_ids = set()
        unique_documents = []
        unique_metadata = []

        for chunk_id, doc, meta in zip(all_ids, all_documents, all_metadata):
            if chunk_id not in seen_ids:
                seen_ids.add(chunk_id)
                unique_documents.append(doc)
                unique_metadata.append(meta)

        logger.info(
            f"Deduplicated: {len(all_documents)} -> {len(unique_documents)} documents"
        )

        return unique_documents, unique_metadata


# Singleton instance for dependency injection
def get_chat_service(
    llm_client_instance=None,
    planner_config: Optional[PlannerConfig] = None,
    session_store=None,
) -> ChatService:
    """
    Factory function for creating ChatService instances.

    Args:
        llm_client_instance: LLM client instance
        planner_config: Planner configuration

    Returns:
        ChatService instance
    """
    return ChatService(
        llm_client_instance=llm_client_instance,
        planner_config=planner_config,
        session_store=session_store,
    )
