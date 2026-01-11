from ..core import db_client
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import JSON
from datetime import datetime, timezone
from sqlalchemy.orm import relationship


class Chat(db_client.Base):

    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    chat_name = Column(String, nullable=False, unique=True)
    chat_history = Column(JSON, nullable=False, default=list)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # One-to-many relationship: a Chat can have many Documents
    documents = relationship(
        "Document",
        back_populates="chat",
        cascade="all, delete-orphan",
    )
