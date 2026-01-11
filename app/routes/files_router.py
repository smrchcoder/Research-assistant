from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from ..services import FileService, TextChunker, EmbeddingService
from typing import List, Dict, Any
from ..core import vector_db_client, settings, db_client
from ..repositories import DocumentRepository, ChatRepository
from ..exceptions import DocumentAlreadyExistsError, FileProcessingError
from sqlalchemy.exc import SQLAlchemyError
import logging
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
file_router = APIRouter()


@file_router.post("/upload/files")
async def upload_files(
    chat_id: int = Form(..., description="Chat ID to associate documents with"),
    files: List[UploadFile] = File(...),
    db: Session = Depends(db_client.get_db),
) -> Dict[str, Any]:
    """
    Upload and process PDF files through all 5 stages:
    Stage 1: Upload files
    Stage 2: Extract text and clean data
    Stage 3: Chunk the cleaned text
    Stage 4: Generate embeddings
    Stage 5: Store in vector database

    Returns:
        Dictionary with processing results and statistics
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    logger.info(f"Processing {len(files)} file(s) for chat_id: {chat_id}")

    # Initialize services
    file_service = FileService()
    text_chunker = TextChunker(
        chunk_size=settings.chunk_size, overlap_size=settings.chunk_overlap
    )
    embedding_service = EmbeddingService()
    document_repo = DocumentRepository(db)
    chat_repo = ChatRepository(db)

    # Verify chat exists
    chat = chat_repo.get_chat_by_id(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail=f"Chat with ID {chat_id} not found")

    results = []
    all_chunks = []

    # Stages 1-3: Extract, clean, and chunk documents
    for file in files:
        document = None
        try:
            logger.info(f"Processing file: {file.filename}")

            # Check if document already exists in vector DB
            if vector_db_client.check_document_exists(file.filename):
                logger.warning(f"Document {file.filename} already exists in database")
                results.append(
                    {
                        "filename": file.filename,
                        "status": "skipped",
                        "reason": "Document already exists in database",
                    }
                )
                continue

            # Create document record in database with 'processing' status
            try:
                document = document_repo.create_document(file.filename)
            except DocumentAlreadyExistsError:
                # Document already exists in PostgreSQL
                logger.warning(f"Document {file.filename} already exists in PostgreSQL")
                results.append(
                    {
                        "filename": file.filename,
                        "status": "skipped",
                        "reason": "Document metadata already exists",
                    }
                )
                continue
            except SQLAlchemyError as e:
                # Database error - this is a real error, not a skip
                logger.error(
                    f"Database error creating document record for {file.filename}: {e}"
                )
                results.append(
                    {
                        "filename": file.filename,
                        "status": "failed",
                        "error": "Database error occurred",
                    }
                )
                continue

            # Stage 1 & 2: Upload, extract, and clean
            extracted_pages = await file_service.upload_file(file)

            # Get the file path from file_service (assuming it stores the file and returns path)
            file_path = f"{settings.upload_directory}/{file.filename}"

            # Stage 3: Generate chunks from cleaned pages
            chunks = text_chunker.generate_chunks(
                document_id=file.filename, document=extracted_pages
            )

            # Update document metadata with pages, chunks count, and file path
            document_repo.update_document_metadata(
                filename=file.filename,
                no_of_pages=len(extracted_pages),
                total_chunks=len(chunks),
                path=file_path,
            )

            # Associate document with chat
            try:
                document_repo.add_chat_to_document(document.id, chat_id)
                logger.info(f"Associated document {file.filename} with chat {chat_id}")
            except Exception as assoc_error:
                logger.error(f"Failed to associate document with chat: {assoc_error}")

            all_chunks.extend(chunks)

            results.append(
                {
                    "filename": file.filename,
                    "status": "success",
                    "pages_count": len([p for p in extracted_pages.values() if p]),
                    "chunks_count": len(chunks),
                }
            )

            logger.info(
                f"Successfully processed {file.filename}: "
                f"{len(chunks)} chunks from {len(extracted_pages)} pages"
            )

        except FileProcessingError as e:
            # File processing failed - user-facing error
            logger.error(f"File processing error for {file.filename}: {e.reason}")

            if document:
                try:
                    document_repo.mark_as_failed(file.filename)
                except Exception as db_error:
                    logger.error(f"Failed to update document status: {db_error}")

            results.append(
                {
                    "filename": file.filename,
                    "status": "failed",
                    "error": e.reason,  # User-friendly message
                }
            )

        except SQLAlchemyError as e:
            # Database error
            logger.error(f"Database error for {file.filename}: {e}")

            if document:
                try:
                    document_repo.mark_as_failed(file.filename)
                except Exception as db_error:
                    logger.error(f"Failed to update document status: {db_error}")

            results.append(
                {
                    "filename": file.filename,
                    "status": "failed",
                    "error": "Database operation failed",
                }
            )

        except Exception as e:
            # Unexpected error - log details but show generic message
            logger.error(
                f"Unexpected error processing {file.filename}: {e}", exc_info=True
            )

            # Mark document as failed in database if it was created
            if document:
                try:
                    document_repo.mark_as_failed(file.filename)
                except Exception as db_error:
                    logger.error(f"Failed to update document status: {db_error}")

            results.append(
                {
                    "filename": file.filename,
                    "status": "failed",
                    "error": "An unexpected error occurred during processing",
                }
            )

    # Stage 4 & 5: Generate embeddings and store in vector DB
    storage_stats = {"stored": 0, "skipped": 0, "errors": 0}

    if all_chunks:
        try:
            logger.info(f"Generating embeddings for {len(all_chunks)} chunks")

            # Stage 4: Generate embeddings
            chunks_with_embeddings = embedding_service.generate_embeddings(all_chunks)

            # Stage 5: Store in ChromaDB
            logger.info("Storing chunks in vector database")
            storage_stats = vector_db_client.store_chunks(chunks_with_embeddings)

            # Mark successfully processed documents as completed
            for result in results:
                if result["status"] == "success":
                    try:
                        document_repo.mark_as_completed(result["filename"])
                    except SQLAlchemyError as db_error:
                        logger.error(
                            f"Database error marking {result['filename']} as completed: {db_error}"
                        )
                    except Exception as db_error:
                        logger.error(
                            f"Unexpected error marking {result['filename']} as completed: {db_error}"
                        )

        except Exception as e:
            logger.error(f"Error in embedding/storage pipeline: {e}", exc_info=True)

            # Mark all documents that were being processed as failed
            for result in results:
                if result["status"] == "success":
                    result["embedding_error"] = "Embedding generation failed"
                    try:
                        document_repo.mark_as_failed(result["filename"])
                    except Exception as db_error:
                        logger.error(f"Failed to update document status: {db_error}")

    logger.info(
        f"Processing complete: {len([r for r in results if r['status'] == 'success'])} succeeded, "
        f"{len([r for r in results if r['status'] == 'failed'])} failed, "
        f"{len([r for r in results if r['status'] == 'skipped'])} skipped"
    )

    return {
        "total_files": len(files),
        "successful": len([r for r in results if r["status"] == "success"]),
        "failed": len([r for r in results if r["status"] == "failed"]),
        "skipped": len([r for r in results if r["status"] == "skipped"]),
        "storage_stats": storage_stats,
        "results": results,
    }
