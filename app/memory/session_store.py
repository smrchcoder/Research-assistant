from .redis_client import redis_client
from ..core.config import settings
import uuid
from datetime import datetime, timezone
import json
import logging
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)

class SessionStore:
    """Manages user chat sessions in Redis with conversation history"""
    
    def __init__(self):
        self.client = redis_client
        self.session_prefix = "session"
        self.ttl = settings.session_ttl_seconds

    def create_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Create a new session for a user
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            Dictionary with session details or None if creation fails
        """
        session_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()

        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "conversations": [],
            "created_at": created_at,
            "updated_at": created_at,
        }
        
        try:
            # Store session in Redis with expiration
            self.client.set(
                name=f"{self.session_prefix}:{session_id}",
                value=json.dumps(session_data),
                ex=self.ttl,
            )
            
            logger.info(f"Session created: {session_id} for user: {user_id}")
            
            return {
                "session_id": session_id,
                "user_id": user_id,
                "created_at": created_at,
                "expires_in_seconds": self.ttl
            }
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return None

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data from Redis
        
        Args:
            session_id: The session identifier
            
        Returns:
            Session data dictionary or None if not found
        """
        try:
            data = self.client.get(name=f"{self.session_prefix}:{session_id}")
            if data:
                return json.loads(data)
            logger.warning(f"Session not found: {session_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None

    def add_message(self, session_id: str, question: str, answer:str) -> bool:
        """Add a message to the conversation history
        
        Args:
            session_id: The session identifier
            role: Message role (user, assistant, system)
            content: Message content
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session_data = self.get_session(session_id)
            if not session_data:
                logger.error(f"Cannot add message - session not found: {session_id}")
                return False
            
            # Add new message
            message = {
                "question": question,
                "answer":answer,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            session_data["conversations"].append(message)
            session_data["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            # Update session in Redis and refresh TTL
            self.client.set(
                name=f"{self.session_prefix}:{session_id}",
                value=json.dumps(session_data),
                ex=self.ttl,
            )
            
            logger.info(f"Message added to session {session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to add message to session {session_id}: {e}")
            return False

    def get_conversation_history(self, session_id: str) -> List[Dict[str, str]]:
        """Get conversation history for a session
        
        Args:
            session_id: The session identifier
            
        Returns:
            List of conversation messages
        """
        session_data = self.get_session(session_id)
        if session_data:
            return session_data.get("conversations", [])
        return []

    def delete_session(self, session_id: str) -> bool:
        """Delete a session from Redis
        
        Args:
            session_id: The session identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.client.delete(f"{self.session_prefix}:{session_id}")
            if result:
                logger.info(f"Session deleted: {session_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False

    def extend_session(self, session_id: str) -> bool:
        """Extend session expiration time
        
        Args:
            session_id: The session identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.client.expire(name=f"{self.session_prefix}:{session_id}", time=self.ttl)
            if result:
                logger.info(f"Session extended: {session_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to extend session {session_id}: {e}")
            return False


# Create singleton instance
session_store = SessionStore()
