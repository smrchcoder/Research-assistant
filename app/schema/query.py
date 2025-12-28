from pydantic import BaseModel, Field, ConfigDict
from typing import List

class SourceInfo(BaseModel):
    """Information about a source document"""
    document_id: str
    page_number: int | str
    chunk_id: str


class QueryRequest(BaseModel):
    """Request model for query endpoint"""
    query: str = Field(..., min_length=1, description="User's question")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of documents to retrieve")
    temperature: float = Field(default=0.3, ge=0, le=2, description="LLM temperature")
    model: str = Field(default="gpt-4o-mini", description="OpenAI model to use")


class QueryResponse(BaseModel):
    """Response model for query endpoint"""
    query_id: str
    query: str
    answer: str
    sources: List[SourceInfo]
    num_sources: int
    
    model_config=ConfigDict(from_attributes=True)
    # class Config:
    #     json_schema_extra = {
    #         "example": {
    #             "query_id": "123e4567-e89b-12d3-a456-426614174000",
    #             "query": "What is machine learning?",
    #             "answer": "Based on the provided context, machine learning is...",
    #             "sources": [
    #                 {
    #                     "document_id": "ai_introduction.pdf",
    #                     "page_number": 5,
    #                     "chunk_id": "chunk_001"
    #                 }
    #             ],
    #             "num_sources": 1
    #         }
    #     }
