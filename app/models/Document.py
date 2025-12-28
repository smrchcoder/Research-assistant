from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from ..core.relation_database import db_client


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
    status = Column(String, nullable=False, default="pending")  # pending, processing, completed, failed
    uploaded_at = Column(DateTime, nullable=False, default=datetime.now)
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', status='{self.status}', pages={self.no_of_pages}, chunks={self.total_chunks})>"
