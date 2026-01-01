from openai import OpenAI
from ..core.config import settings
import logging

logger = logging.getLogger(__name__)


class LLMClient:
    """OpenAI client wrapper for embeddings and other LLM operations"""
    
    def __init__(self):
        """Initialize OpenAI client with API key from settings"""
        try:
            self._client = OpenAI(api_key=settings.openai_api_key)
            logger.info("OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise
    
    @property
    def client(self) -> OpenAI:
        """Get the underlying OpenAI client"""
        return self._client
    # todo
    @property
    def embeddings(self):
        """Access to embeddings API"""
        return self._client.embeddings
    


# Create singleton instance
llm_client = LLMClient()
