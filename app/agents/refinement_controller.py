"""Refinement controller for managing iterative retrieval refinement."""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RefinementController:
    """Controller for managing iterative refinement of retrieval results."""
    
    def __init__(self, max_iterations: int = 3, min_confidence: float = 0.7):
        """
        Initialize refinement controller.
        
        Args:
            max_iterations: Maximum number of refinement iterations
            min_confidence: Minimum confidence score to consider sufficient
        """
        self.max_iterations = max_iterations
        self.min_confidence = min_confidence
        self.current_iteration = 0
        self.refinement_history: List[Dict[str, Any]] = []
    
    def should_refine(self, evaluation: Dict[str, Any]) -> bool:
        """
        Determine if refinement should continue.
        
        Args:
            evaluation: Evaluation result from Evaluator agent
            
        Returns:
            True if refinement should continue, False otherwise
        """
        if self.current_iteration >= self.max_iterations:
            logger.info(f"Max iterations ({self.max_iterations}) reached")
            return False
        
        is_sufficient = evaluation.get('is_sufficient', False)
        confidence = evaluation.get('confidence_score', 0.0)
        
        if is_sufficient and confidence >= self.min_confidence:
            logger.info(f"Results sufficient with confidence {confidence}")
            return False
        
        logger.info(
            f"Iteration {self.current_iteration + 1}: Results insufficient "
            f"(is_sufficient={is_sufficient}, confidence={confidence})"
        )
        return True
    
    def generate_refinement_queries(self, evaluation: Dict[str, Any], original_query: str) -> List[str]:
        """
        Generate new search queries based on evaluator feedback.
        
        Args:
            evaluation: Evaluation result with missing_aspects and suggested_followups
            original_query: The original user query
            
        Returns:
            List of refinement queries
        """
        refinement_queries = []
        
        # Use suggested followups from evaluator
        suggested_followups = evaluation.get('suggested_followups', [])
        for followup in suggested_followups[:2]:  # Limit to 2 followups
            refinement_queries.append(followup)
        
        # Generate queries for missing aspects
        missing_aspects = evaluation.get('missing_aspects', [])
        for aspect in missing_aspects[:2]:  # Limit to 2 aspects
            refinement_queries.append(f"{original_query} - {aspect}")
        
        logger.info(f"Generated {len(refinement_queries)} refinement queries")
        return refinement_queries
    
    def record_iteration(self, evaluation: Dict[str, Any], documents_retrieved: int) -> None:
        """
        Record details of a refinement iteration.
        
        Args:
            evaluation: Evaluation result
            documents_retrieved: Number of documents retrieved in this iteration
        """
        self.current_iteration += 1
        self.refinement_history.append({
            'iteration': self.current_iteration,
            'is_sufficient': evaluation.get('is_sufficient', False),
            'confidence_score': evaluation.get('confidence_score', 0.0),
            'documents_retrieved': documents_retrieved,
            'missing_aspects': evaluation.get('missing_aspects', []),
            'suggested_followups': evaluation.get('suggested_followups', [])
        })
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of refinement process.
        
        Returns:
            Dictionary with refinement summary
        """
        return {
            'total_iterations': self.current_iteration,
            'max_iterations': self.max_iterations,
            'refinement_history': self.refinement_history
        }