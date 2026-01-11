from pydantic import BaseModel, Field
from typing import List


class StartChatRequest(BaseModel):
    """Request model for starting a chat session"""

    user_id: str = Field(..., description="Unique identifier for the user")
    chat_name: str= Field(..., description="ChatName for the newly created chat")
    


class StartChatResponse(BaseModel):
    """Response model for chat session creation"""

    chat_id: int
    session_id: str
    user_id: str
    created_at: str
    expires_in_seconds: int
    message: str = "Chat session created successfully"


class ChatQueryRequest(BaseModel):
    session_id: str = Field(..., description="Session id for the chat initilized")
    chat_id: int = Field(..., description="Chat ID to identify which documents to query")
    query: str = Field(..., description="Query provided by the user")
