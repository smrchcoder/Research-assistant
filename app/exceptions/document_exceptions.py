"""
Custom exceptions for document processing.

Following best practices:
- Specific exception types for different error scenarios
- Clear, user-friendly error messages
- Separation of internal errors from user-facing errors
"""


class DocumentError(Exception):
    """Base exception for document-related errors"""
    pass


class DocumentAlreadyExistsError(DocumentError):
    """Raised when attempting to create a document that already exists"""
    def __init__(self, filename: str):
        self.filename = filename
        super().__init__(f"Document '{filename}' already exists")


class DocumentNotFoundError(DocumentError):
    """Raised when a document cannot be found"""
    def __init__(self, filename: str):
        self.filename = filename
        super().__init__(f"Document '{filename}' not found")


class DocumentProcessingError(DocumentError):
    """Raised when document processing fails"""
    def __init__(self, filename: str, reason: str):
        self.filename = filename
        self.reason = reason
        super().__init__(f"Failed to process document '{filename}': {reason}")


class FileProcessingError(Exception):
    """Raised when file upload or extraction fails"""
    def __init__(self, filename: str, reason: str):
        self.filename = filename
        self.reason = reason
        super().__init__(f"Failed to process file '{filename}': {reason}")
