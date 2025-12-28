from ..core import llm_client, settings
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings using OpenAI API"""
    
    def __init__(self):
        self.model = settings.openai_embedding_model
        self.batch_size = settings.embedding_batch_size
    
    def generate_embeddings(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate embeddings for text chunks using OpenAI API
        
        Args:
            chunks: List of chunk dictionaries with 'text' field
            
        Returns:
            List of chunks with 'embeddings' field added
        """
        if not chunks:
            logger.warning("No chunks provided for embedding generation")
            return chunks
        
        logger.info(f"Generating embeddings for {len(chunks)} chunks")
        
        try:
            # Process in batches to avoid rate limits
            for batch_start in range(0, len(chunks), self.batch_size):
                batch_end = min(batch_start + self.batch_size, len(chunks))
                batch_chunks = chunks[batch_start:batch_end]
                
                # Extract text from chunks
                batch_texts = [chunk['text'] for chunk in batch_chunks]
                
                logger.info(
                    f"Processing batch {batch_start // self.batch_size + 1}: "
                    f"chunks {batch_start}-{batch_end-1}"
                )
                
                # Call OpenAI API
                response = llm_client.embeddings.create(
                    model=self.model,
                    input=batch_texts,
                    encoding_format="float"
                )
                
                # Add embeddings to chunks (fix: use batch_chunks, not all chunks)
                for chunk, embedding_obj in zip(batch_chunks, response.data):
                    chunk['embeddings'] = embedding_obj.embedding
                
                logger.debug(f"Batch {batch_start // self.batch_size + 1} completed")
            
            logger.info(f"Successfully generated embeddings for {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise Exception(f"Embedding generation failed: {str(e)}")
