from fastapi import FastAPI
from .routes import file_router, chat_router
from .core import settings, vector_db_client, db_client
from .memory.redis_client import redis_client
import logging
from sqlalchemy import text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("app.log")],
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Document Processing API",
    description="API for processing PDF documents through extraction, cleaning, and chunking stages",
    version="1.0.0",
)


@app.get("/health")
def health_check():
    """Health check endpoint"""
    db_status = "unknown"
    redis_status = "unknown"
    
    try:
        # Test database connection
        with db_client.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    try:
        # Test Redis connection
        redis_client.ping()
        redis_status = "healthy"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        redis_status = "unhealthy"
    
    overall_healthy = db_status == "healthy" and redis_status == "healthy"
    
    return {
        "status": "healthy" if overall_healthy else "degraded",
        "message": "API is running",
        "database": db_status,
        "redis": redis_status,
        "vector_db_items": vector_db_client.collection.count(),
        "settings": {
            "chunk_size": settings.chunk_size,
            "chunk_overlap": settings.chunk_overlap,
            "embedding_model": settings.openai_embedding_model,
            "session_ttl_seconds": settings.session_ttl_seconds,
        },
    }


# Include routers with prefix
app.include_router(file_router, prefix="/api", tags=["documents"])
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])

# # Include router for query
# app.include_router(query_router, tags=['queries'])
