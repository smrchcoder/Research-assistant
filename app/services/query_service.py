import uuid
from ..core import settings, vector_db_client
from ..llm import llm_client
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class QueryService:
    """Service for handling query processing and answer generation"""

    def __init__(self, query: str):
        self.query = query.strip()
        self.query_id = str(uuid.uuid4())
        self.embedding_model = settings.openai_embedding_model

    def retrieve_similarities(self, top_k: int = 5, document_filenames: List[str] = None) -> Dict[str, Any]:
        """
        Retrieve similar documents from vector database

        Args:
            top_k: Number of top results to return
            document_filenames: Optional list of document filenames to filter by

        Returns:
            Search results with documents and metadata
        """
        embeddings = self.convert_query_to_embeddings()
        modified_top_k = min(5, top_k)
        return self.query_embeddings(top_k=modified_top_k, embeddings=embeddings, document_filenames=document_filenames)

    def convert_query_to_embeddings(self) -> List[float]:
        """
        Convert query text to embedding vector

        Returns:
            Embedding vector as list of floats
        """
        try:
            response = llm_client.embeddings.create(
                model=self.embedding_model, input=self.query, encoding_format="float"
            )
            embedding = response.data[0].embedding
            logger.info(f"Generated embeddings for query: {self.query_id}")
            return embedding
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise

    def query_embeddings(self, embeddings: List[float], top_k: int, document_filenames: List[str] = None) -> Dict[str, Any]:
        """
        Search vector database with embedding vector

        Args:
            embeddings: Query embedding vector
            top_k: Number of results to return
            document_filenames: Optional list of document filenames to filter by

        Returns:
            Search results from vector database
        """
        try:
            # Build where filter if document_filenames provided
            where_filter = None
            if document_filenames:
                where_filter = {"document_id": {"$in": document_filenames}}
                logger.info(f"Filtering query by {len(document_filenames)} documents")
            
            results = vector_db_client.search_similar(embeddings, n_results=top_k, where=where_filter)
            logger.info(f"Retrieved {len(results.get('documents', [[]])[0])} documents")
            return results
        except Exception as e:
            logger.error(f"Error querying vector database: {e}")
            raise

    def generate_answer(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4o-mini",
        temperature: float = 0.3,
        max_tokens: int = 1000,
    ) -> str:
        """
        Generate answer using OpenAI chat completion

        Args:
            messages: List of message dictionaries for chat API
            model: Model name to use
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response

        Returns:
            Generated answer text
        """
        try:
            response = llm_client.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            answer = response.choices[0].message.content
            logger.info(f"Generated answer for query: {self.query_id}")
            return answer

        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            raise
