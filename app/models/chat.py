from pydantic import BaseModel, Field
from typing import List


class StartChatRequest(BaseModel):
    """Request model for starting a chat session"""

    user_id: str = Field(..., description="Unique identifier for the user")


class StartChatResponse(BaseModel):
    """Response model for chat session creation"""

    session_id: str
    user_id: str
    created_at: str
    expires_in_seconds: int
    message: str = "Chat session created successfully"


class ChatQueryRequest(BaseModel):
    session_id: str = Field(..., description="Session id for the chat initilized")
    document_ids: List[str] = Field(
        default=[], description="List of all documents uploaded for this session"
    )
    query:str= Field(..., description="Query provided by the user")
