from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List
import logging

from ..schema import Document, Chat
from ..exceptions import DocumentAlreadyExistsError, DocumentNotFoundError

logger = logging.getLogger(__name__)


class DocumentRepository:
    """Repository for handling Document database operations"""

    def __init__(self, db: Session):
        self.db = db

    def create_document(self, filename: str, path: Optional[str] = None) -> Optional[Document]:
        """
        Create a new document record in the database
        
        Args:
            filename: Name of the document
            
        Returns:
            Created Document object
            
        Raises:
            DocumentAlreadyExistsError: If document with filename already exists
            SQLAlchemyError: For database errors
        """
        # Check if document already exists
        existing_doc = self.get_by_filename(filename)
        if existing_doc:
            raise DocumentAlreadyExistsError(filename)
        
        try:
            new_document = Document(
                filename=filename,
                no_of_pages=0,
                total_chunks=0,
                status="processing",
                path=path,
            )
            
            self.db.add(new_document)
            self.db.commit()
            self.db.refresh(new_document)
            
            logger.info(f"Created document record: {filename}")
            return new_document
            
        except SQLAlchemyError as e:
            logger.error(f"Database error creating document '{filename}': {e}")
            self.db.rollback()
            raise

    def get_by_filename(self, filename: str) -> Optional[Document]:
        """
        Get document by filename
        
        Args:
            filename: Name of the document
            
        Returns:
            Document object or None if not found
        """
        try:
            return self.db.query(Document).filter(Document.filename == filename).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching document '{filename}': {e}")
            raise

    def get_by_id(self, document_id: int) -> Optional[Document]:
        """
        Get document by ID
        
        Args:
            document_id: ID of the document
            
        Returns:
            Document object or None if not found
        """
        try:
            return self.db.query(Document).filter(Document.id == document_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching document ID {document_id}: {e}")
            raise

    def update_document_metadata(
        self,
        filename: str,
        no_of_pages: Optional[int] = None,
        total_chunks: Optional[int] = None,
        status: Optional[str] = None,
        path: Optional[str] = None,
    ) -> Optional[Document]:
        """
        Update document metadata
        
        Args:
            filename: Name of the document
            no_of_pages: Number of pages in the document
            total_chunks: Total number of chunks
            status: Processing status
            
        Returns:
            Updated Document object
            
        Raises:
            DocumentNotFoundError: If document not found
            SQLAlchemyError: For database errors
        """
        document = self.get_by_filename(filename)
        if not document:
            raise DocumentNotFoundError(filename)
        
        try:
            # Update only provided fields
            if no_of_pages is not None:
                document.no_of_pages = no_of_pages
            if total_chunks is not None:
                document.total_chunks = total_chunks
            if status is not None:
                document.status = status
            if path is not None:
                document.path = path
            
            self.db.commit()
            self.db.refresh(document)
            
            logger.info(f"Updated document metadata: {filename}")
            return document
            
        except SQLAlchemyError as e:
            logger.error(f"Database error updating document '{filename}': {e}")
            self.db.rollback()
            raise

    def mark_as_completed(self, filename: str) -> Optional[Document]:
        """
        Mark document as completed
        
        Args:
            filename: Name of the document
            
        Returns:
            Updated Document object
        """
        return self.update_document_metadata(filename, status="completed")

    def mark_as_failed(self, filename: str) -> Optional[Document]:
        """
        Mark document as failed
        
        Args:
            filename: Name of the document
            
        Returns:
            Updated Document object
        """
        return self.update_document_metadata(filename, status="failed")

    def get_all_documents(self, skip: int = 0, limit: int = 100) -> List[Document]:
        """
        Get all documents with pagination
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of Document objects
        """
        try:
            return self.db.query(Document).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching documents: {e}")
            raise

    def delete_document(self, filename: str) -> bool:
        """
        Delete a document record
        
        Args:
            filename: Name of the document
            
        Returns:
            True if deleted, False if not found
        """
        try:
            document = self.get_by_filename(filename)
            if not document:
                return False
            # dissociate chat to be safe before deletion
            if hasattr(document, "chat") and document.chat is not None:
                document.chat = None
            self.db.delete(document)
            self.db.commit()
            
            logger.info(f"Deleted document: {filename}")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Database error deleting document '{filename}': {e}")
            self.db.rollback()
            raise

    def add_chat_to_document(self, document_id: int, chat_id: int) -> Optional[Document]:
        """Associate a chat with a document (one-to-many)

        This sets `document.chat_id = chat_id`.
        """
        document = self.get_by_id(document_id)
        if not document:
            raise DocumentNotFoundError(document_id)

        try:
            chat = self.db.query(Chat).filter(Chat.id == chat_id).first()
            if not chat:
                return None

            document.chat = chat
            self.db.commit()
            self.db.refresh(document)

            return document
        except SQLAlchemyError as e:
            logger.error(f"Database error associating chat {chat_id} to document {document_id}: {e}")
            self.db.rollback()
            raise

    def remove_chat_from_document(self, document_id: int, chat_id: int) -> Optional[Document]:
        """
        Remove association between a chat and a document (one-to-many)
        """
        document = self.get_by_id(document_id)
        if not document:
            raise DocumentNotFoundError(document_id)

        try:
            # Only clear if the document is assigned to the provided chat_id
            if document.chat_id == chat_id:
                document.chat = None
                self.db.commit()
                self.db.refresh(document)

            return document
        except SQLAlchemyError as e:
            logger.error(f"Database error removing chat {chat_id} from document {document_id}: {e}")
            self.db.rollback()
            raise

    def list_chats_for_document(self, document_id: int) -> List[Chat]:
        """
        Return the chat associated with the given document (one-to-many)
        """
        document = self.get_by_id(document_id)
        if not document:
            raise DocumentNotFoundError(document_id)

        return [document.chat] if document.chat is not None else []

    def list_documents_for_chat(self, chat_id: int, skip: int = 0, limit: int = 100) -> List[Document]:
        """
        Return documents associated with a chat (paginated)
        """
        try:
            chat = self.db.query(Chat).filter(Chat.id == chat_id).first()
            if not chat:
                return []

            # apply pagination on the list of documents
            return chat.documents[skip: skip + limit]
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching documents for chat {chat_id}: {e}")
            raise
