from sqlalchemy.orm import Session
from ..schema import Chat
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)


class ChatRepository:

    def __init__(self, db: Session):
        self.db = db

    def create_chat(self, chat_name):
        chat = self.get_chat_by_chat_name(chat_name)
        if chat:
            raise Exception("chat already exist")
        try:
            new_chat = Chat(chat_name=chat_name)
            self.db.add(new_chat)
            self.db.commit()
            self.db.refresh(new_chat)
            return new_chat
        except SQLAlchemyError as e:
            logger.error(f"Error creating chat record: {e}")
            self.db.rollback()
            raise

    def get_chat_by_chat_name(self, chat_name):
        try:
            return self.db.query(Chat).filter(Chat.chat_name == chat_name).first()
        except SQLAlchemyError as e:
            logger.error(
                f"Database error querying database for chat name {chat_name}, error {e}"
            )
            raise

    def get_chat_by_id(self, chat_id: int):
        """Get chat by ID"""
        try:
            return self.db.query(Chat).filter(Chat.id == chat_id).first()
        except SQLAlchemyError as e:
            logger.error(
                f"Database error querying database for chat ID {chat_id}, error {e}"
            )
            raise

    def update_chat_history(self, chat_id: int, query: str, answer: str):
        """Append query and answer to chat history"""
        try:
            chat = self.get_chat_by_id(chat_id)
            if not chat:
                raise ValueError(f"Chat with ID {chat_id} not found")

            # Append to chat_history (it's a JSON array)
            history = chat.chat_history or []
            history.append({"query": query, "answer": answer})
            chat.chat_history = history

            self.db.commit()
            self.db.refresh(chat)
            return chat
        except SQLAlchemyError as e:
            logger.error(
                f"Database error updating chat history for chat ID {chat_id}, error {e}"
            )
            self.db.rollback()
            raise
