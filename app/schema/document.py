from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from sqlalchemy.orm import relationship

from ..core import db_client


class Document(db_client.Base):
    """
    SQLAlchemy model for document metadata

    Represents metadata about uploaded PDF documents including
    processing status, page count, and chunk information.
    """

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename = Column(String, nullable=False, index=True, unique=True)
    no_of_pages = Column(Integer, nullable=False, default=0)
    total_chunks = Column(Integer, nullable=False, default=0)
    status = Column(
        String, nullable=False, default="pending"
    )  # pending, processing, completed, failed
    uploaded_at = Column(DateTime, nullable=False, default=datetime.now)
    # Filesystem path where the uploaded PDF is stored (optional)
    path = Column(String, nullable=True, index=False)

    # One-to-many: Document belongs to a single Chat
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), nullable=True, index=True)
    chat = relationship("Chat", back_populates="documents")

    def __repr__(self):
        return (
            f"<Document(id={self.id}, filename='{self.filename}', status='{self.status}', "
            f"pages={self.no_of_pages}, chunks={self.total_chunks}, path={self.path})>"
        )
