from pydantic_settings import BaseSettings
from pydantic import Field
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small",
        env="OPENAI_EMBEDDING_MODEL"
    )
    embedding_batch_size: int = Field(default=100, env="EMBEDDING_BATCH_SIZE")
    
    # Database Configuration
    database_url: str = Field(
        default="postgresql+psycopg2://user:password@localhost:5432/multi-agent",
        env="DATABASE_URL"
    )
    db_echo: bool = Field(default=False, env="DB_ECHO")
    
    # ChromaDB Configuration
    chroma_persist_directory: str = Field(
        default="./chroma_db",
        env="CHROMA_PERSIST_DIRECTORY"
    )
    chroma_collection_name: str = Field(
        default="document_chunks",
        env="CHROMA_COLLECTION_NAME"
    )
    
    # Text Processing Configuration
    chunk_size: int = Field(default=1000, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, env="CHUNK_OVERLAP")
    
    max_file_size_mb: int = Field(default=50, env="MAX_FILE_SIZE_MB")
    
    # File Upload Configuration
    upload_directory: str = Field(default="./pdfs", env="UPLOAD_DIRECTORY")
    redis_host: str = "localhost"
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")

    session_ttl_seconds: int = Field(default=3600, env="SESSION_TTL_SECONDS")  # 1 hour
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Create settings instance
settings = Settings()

# Ensure required directories exist
os.makedirs(settings.chroma_persist_directory, exist_ok=True)
os.makedirs(settings.upload_directory, exist_ok=True)
