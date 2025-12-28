import chromadb
from chromadb.config import Settings as ChromaSettings
from .config import settings
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class VectorDBClient:
    """ChromaDB client for storing and retrieving document embeddings"""
    
    def __init__(self):
        """Initialize ChromaDB client with persistent storage"""
        try:
            # Create persistent client (automatically creates folder if not exists)
            self._client = chromadb.PersistentClient(
                path=settings.chroma_persist_directory,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            self._collection = self._client.get_or_create_collection(
                name=settings.chroma_collection_name,
                metadata={"description": "Document chunks with embeddings"}
            )
            
            logger.info(
                f"ChromaDB initialized. Collection '{settings.chroma_collection_name}' "
                f"has {self._collection.count()} items"
            )
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    @property
    def collection(self):
        """Get the ChromaDB collection"""
        return self._collection
    
    def store_chunks(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Store document chunks with embeddings in ChromaDB
        
        Args:
            chunks: List of chunk dictionaries with embeddings
            
        Returns:
            Dictionary with storage statistics
        """
        if not chunks:
            logger.warning("No chunks to store")
            return {"stored": 0, "skipped": 0, "errors": 0}
        
        ids = []
        embeddings = []
        documents = []
        metadatas = []
        errors = 0
        
        for chunk in chunks:
            try:
                # Validate chunk has required fields
                if "embeddings" not in chunk or chunk["embeddings"] is None:
                    logger.warning(f"Chunk {chunk.get('chunk_id', 'unknown')} missing embeddings")
                    errors += 1
                    continue
                
                ids.append(chunk["chunk_id"])
                embeddings.append(chunk["embeddings"])
                documents.append(chunk["text"])
                metadatas.append({
                    "document_id": chunk["document_id"],
                    "page_number": chunk.get("page_number", 0),
                    "char_count": chunk.get("char_count", 0),
                    "start_position": chunk.get("start_position", 0),
                    "end_position": chunk.get("end_position", 0)
                })
            except Exception as e:
                logger.error(f"Error processing chunk: {e}")
                errors += 1
                continue
        
        if not ids:
            logger.error("No valid chunks to store")
            return {"stored": 0, "skipped": len(chunks), "errors": errors}
        
        try:
            # Add to ChromaDB (automatically persists with PersistentClient)
            self._collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            
            logger.info(f"Stored {len(ids)} chunks in ChromaDB")
            return {
                "stored": len(ids),
                "skipped": len(chunks) - len(ids),
                "errors": errors,
                "total_in_collection": self._collection.count()
            }
        except Exception as e:
            logger.error(f"Failed to store chunks in ChromaDB: {e}")
            raise
    
    def search_similar(self, query_embedding: List[float], n_results: int = 5) -> Dict[str, Any]:
        """
        Search for similar chunks using embedding similarity
        
        Args:
            query_embedding: Query embedding vector
            n_results: Number of results to return
            
        Returns:
            Dictionary with search results
        """
        try:
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            return results
        except Exception as e:
            logger.error(f"Failed to search ChromaDB: {e}")
            raise
    
    def check_document_exists(self, document_id: str) -> bool:
        """
        Check if a document already exists in the database
        
        Args:
            document_id: Document identifier
            
        Returns:
            True if document exists, False otherwise
        """
        try:
            results = self._collection.get(
                where={"document_id": document_id}
            )
            return len(results["ids"]) > 0
        except Exception as e:
            logger.error(f"Error checking document existence: {e}")
            return False


# Create singleton instance
vector_db_client = VectorDBClient()
