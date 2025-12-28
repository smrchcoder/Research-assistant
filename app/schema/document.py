from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class DocumentBase(BaseModel):
    """Base schema for Document with common fields"""
    filename: str = Field(..., description="Name of the uploaded document")
    

class DocumentCreate(DocumentBase):
    """Schema for creating a new document"""
    pass


class DocumentUpdate(BaseModel):
    """Schema for updating document metadata"""
    no_of_pages: Optional[int] = Field(None, ge=0, description="Number of pages in the document")
    total_chunks: Optional[int] = Field(None, ge=0, description="Total number of text chunks")
    status: Optional[str] = Field(None, description="Processing status (pending, processing, completed, failed)")


class DocumentResponse(DocumentBase):
    """Schema for document response"""
    id: int = Field(..., description="Unique document identifier")
    no_of_pages: int = Field(0, ge=0, description="Number of pages in the document")
    total_chunks: int = Field(0, ge=0, description="Total number of text chunks")
    status: str = Field("pending", description="Processing status")
    uploaded_at: datetime = Field(..., description="Timestamp when document was uploaded")
    
    model_config = ConfigDict(from_attributes=True)
# model_config converts ORM object to Pydantic Model

class DocumentListResponse(BaseModel):
    """Schema for listing multiple documents"""
    total: int = Field(..., description="Total number of documents")
    documents: list[DocumentResponse] = Field(..., description="List of documents")
    
    model_config = ConfigDict(from_attributes=True)