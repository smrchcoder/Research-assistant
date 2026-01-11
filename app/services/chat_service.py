"""
Chat service layer for handling chat-related business logic.
"""

from typing import Dict, Any, List, Optional
import logging
from ..agents import Planner, Retriever, Evaluator, Synthesizer, RefinementController
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
        max_refinement_iterations: int = 3,
        min_confidence_threshold: float = 0.7,
    ):
        """
        Initialize chat service.

        Args:
            llm_client_instance: LLM client to use (optional, uses default if None)
            planner_config: Configuration for planner agent
            session_store: Session store instance
            max_refinement_iterations: Maximum iterations for refinement loop
            min_confidence_threshold: Minimum confidence score to accept results
        """
        self.llm_client = llm_client_instance
        self.planner_config = planner_config
        self.prompt_template = QueryPromptTemplate()
        self.evaluator = Evaluator(llm_client_instance=self.llm_client)
        self.synthesizer = Synthesizer(llm_client=self.llm_client)
        self.session_store = session_store
        self.max_refinement_iterations = max_refinement_iterations
        self.min_confidence_threshold = min_confidence_threshold

    def process_query(self, session_id: str, query: str, document_filenames: List[str] = None) -> Dict[str, Any]:
        """
        Process a user query: validate session, plan retrieval, and execute with iterative refinement.

        Args:
            session_id: User's session ID
            query: User's question
            document_filenames: Optional list of document filenames to filter by

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
        
        # Initialize refinement controller
        refinement_controller = RefinementController(
            max_iterations=self.max_refinement_iterations,
            min_confidence=self.min_confidence_threshold
        )

        # Retrieve documents based on plan (filtered by document_filenames)
        all_documents, all_metadata = self._retrieve_documents(plan, document_filenames)
        generated_context = self.prompt_template.generate_context(
            documents=all_documents, metadatas=all_metadata
        )
        evaluation = self.evaluator.execute(context=generated_context, query=query)
        
        # Record initial retrieval
        refinement_controller.record_iteration(evaluation, len(all_documents))
        
        # Iterative refinement loop
        while refinement_controller.should_refine(evaluation):
            logger.info(
                f"Refining retrieval - Iteration {refinement_controller.current_iteration + 1}"
            )
            
            # Generate refinement queries based on evaluator feedback
            refinement_queries = refinement_controller.generate_refinement_queries(
                evaluation, query
            )
            
            if not refinement_queries:
                logger.warning("No refinement queries generated, breaking loop")
                break
            
            # Retrieve additional documents for refinement queries
            refinement_docs, refinement_meta = self._retrieve_refinement_documents(
                refinement_queries, document_filenames
            )
            
            # Merge with existing documents (avoiding duplicates)
            all_documents, all_metadata = self._merge_documents(
                all_documents, all_metadata,
                refinement_docs, refinement_meta
            )
            
            # Re-generate context and re-evaluate
            generated_context = self.prompt_template.generate_context(
                documents=all_documents, metadatas=all_metadata
            )
            evaluation = self.evaluator.execute(context=generated_context, query=query)
            
            # Record this iteration
            refinement_controller.record_iteration(evaluation, len(refinement_docs))

        # Collect agent reasoning from all agents
        agent_reasoning = []
        agent_reasoning.extend(plan.get("reasoning", []))
        agent_reasoning.extend(evaluation.get("reasoning", []))

        response = {}
        if evaluation.get("is_sufficient", False):
            # Generate answer if results are sufficient
            response = self.synthesizer.execute(
                context=generated_context,
                session_store=self.session_store,
                session_id=session_id,
                query=query,
                metadatas=all_metadata
            )
            agent_reasoning.extend(response.get("reasoning", []))
        else:
            # Generate fallback response if max iterations reached without sufficient results
            response = self._generate_fallback_response(
                query=query,
                evaluation=evaluation,
                session_id=session_id
            )
            agent_reasoning.extend(response.get("reasoning", []))

        # Calculate processing summary
        agents_used = set(step["agent"] for step in agent_reasoning)

        return {
            "plan": plan,
            "documents": all_documents,
            "query": query,
            "session_id": session_id,
            "evaluation": evaluation,
            "response": response,
            "refinement_summary": refinement_controller.get_summary(),
            "agent_reasoning": agent_reasoning,
            "processing_summary": {
                "total_agents_used": len(agents_used),
                "agents_list": list(agents_used),
                "total_reasoning_steps": len(agent_reasoning),
                "refinement_iterations": refinement_controller.current_iteration,
            },
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

    def _retrieve_documents(self, plan: Dict[str, Any], document_filenames: List[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve documents based on the plan's search queries.

        Args:
            plan: Retrieval plan containing search queries
            document_filenames: Optional list of document filenames to filter by

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

                search_results = retriever.execute(query=query, top_k=top_k, document_filenames=document_filenames)

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
    
    def _retrieve_refinement_documents(
        self, refinement_queries: List[str], document_filenames: List[str] = None
    ) -> tuple[List[str], List[Dict[str, Any]]]:
        """
        Retrieve additional documents for refinement queries.
        
        Args:
            refinement_queries: List of refinement search queries
            document_filenames: Optional list of document filenames to filter by
            
        Returns:
            Tuple of (documents list, metadata list)
        """
        retriever = Retriever()
        all_documents = []
        all_metadata = []
        all_ids = []
        
        for idx, query in enumerate(refinement_queries):
            try:
                if not query:
                    logger.warning(f"Empty refinement query at index {idx}, skipping")
                    continue
                
                search_results = retriever.execute(
                    query=query, top_k=3, document_filenames=document_filenames
                )
                
                # Extract all result components
                ids = search_results.get("ids", [[]])[0]
                documents = search_results.get("documents", [[]])[0]
                metadatas = search_results.get("metadatas", [[]])[0]
                
                all_ids.extend(ids or [])
                all_documents.extend(documents or [])
                all_metadata.extend(metadatas or [])
                
                logger.info(
                    f"Retrieved {len(documents or [])} documents for refinement query: {query[:50]}..."
                )
            except Exception as e:
                logger.error(f"Error retrieving refinement documents for query {idx}: {str(e)}")
                continue
        
        # Remove duplicates
        seen_ids = set()
        unique_documents = []
        unique_metadata = []
        
        for chunk_id, doc, meta in zip(all_ids, all_documents, all_metadata):
            if chunk_id not in seen_ids:
                seen_ids.add(chunk_id)
                unique_documents.append(doc)
                unique_metadata.append(meta)
        
        logger.info(f"Retrieved {len(unique_documents)} unique refinement documents")
        return unique_documents, unique_metadata
    
    def _merge_documents(
        self,
        existing_docs: List[str],
        existing_meta: List[Dict[str, Any]],
        new_docs: List[str],
        new_meta: List[Dict[str, Any]]
    ) -> tuple[List[str], List[Dict[str, Any]]]:
        """
        Merge new documents with existing ones, avoiding duplicates.
        
        Args:
            existing_docs: Existing document list
            existing_meta: Existing metadata list
            new_docs: New document list
            new_meta: New metadata list
            
        Returns:
            Tuple of (merged documents, merged metadata)
        """
        # Track existing documents by a signature (first 100 chars)
        existing_signatures = set(doc[:100] for doc in existing_docs)
        
        merged_docs = existing_docs.copy()
        merged_meta = existing_meta.copy()
        
        for doc, meta in zip(new_docs, new_meta):
            doc_signature = doc[:100]
            if doc_signature not in existing_signatures:
                merged_docs.append(doc)
                merged_meta.append(meta)
                existing_signatures.add(doc_signature)
        
        logger.info(
            f"Merged documents: {len(existing_docs)} existing + {len(new_docs)} new "
            f"= {len(merged_docs)} total (duplicates removed)"
        )
        return merged_docs, merged_meta
    
    def _generate_fallback_response(
        self, query: str, evaluation: Dict[str, Any], session_id: str
    ) -> Dict[str, Any]:
        """
        Generate a fallback response when max iterations reached without sufficient results.
        
        Args:
            query: User's original query
            evaluation: Final evaluation result
            session_id: Session ID
            
        Returns:
            Response dictionary with fallback answer
        """
        missing_aspects = evaluation.get("missing_aspects", [])
        confidence = evaluation.get("confidence_score", 0.0)
        
        fallback_answer = (
            f"I apologize, but I couldn't find sufficient information in the available documents "
            f"to fully answer your question: '{query}'.\n\n"
        )
        
        if missing_aspects:
            fallback_answer += (
                f"The following aspects are missing or insufficiently covered:\n"
            )
            for aspect in missing_aspects:
                fallback_answer += f"- {aspect}\n"
            fallback_answer += "\n"
        
        fallback_answer += (
            f"Confidence in available information: {confidence:.1%}\n\n"
            f"Suggestions:\n"
            f"- Try rephrasing your question\n"
            f"- Upload additional documents that might contain the information\n"
            f"- Ask more specific questions about the available content"
        )
        
        logger.info(f"Generated fallback response for insufficient results")
        
        # Store in session
        try:
            self.session_store.add_message(
                session_id=session_id,
                answer=fallback_answer,
                question=query
            )
        except Exception as e:
            logger.error(f"Failed to update session with fallback: {str(e)}")
        
        return {
            "answer": fallback_answer,
            "citations": [],
            "is_fallback": True,
            "reasoning": [{
                "agent": "ChatService",
                "step_type": "fallback_response",
                "description": "Generated fallback response due to insufficient information",
                "data": {
                    "confidence": confidence,
                    "missing_aspects_count": len(missing_aspects)
                }
            }]
        }


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
