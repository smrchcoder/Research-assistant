from fastapi import APIRouter, HTTPException, status, Depends
from ..models import StartChatRequest, StartChatResponse, ChatQueryRequest
from ..memory.session_store import session_store
import logging
from ..services.chat_service import ChatService, get_chat_service
from ..llm import llm_client
from ..repositories import ChatRepository
from ..core import db_client
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

chat_router = APIRouter()


@chat_router.post(
    "/newchat", response_model=StartChatResponse, status_code=status.HTTP_201_CREATED
)
def start_chat(
    request: StartChatRequest, db: Session = Depends(db_client.get_db)
) -> StartChatResponse:
    """Create a new chat session for a user

    This endpoint creates a new session in Redis that will store
    conversation history for 1 hour (configurable via SESSION_TTL_SECONDS).
    """
    try:
        logger.info(f"Starting chat session for user: {request.user_id}")
        # Create a chat record in database
        chat_repository = ChatRepository(db)
        new_chat = chat_repository.create_chat(chat_name=request.chat_name)

        # Create session in Redis
        session_data = session_store.create_session(request.user_id)

        if not session_data:
            logger.error(f"Failed to create session for user: {request.user_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create chat session",
            )

        # Add chat_id to session data
        session_data["chat_id"] = new_chat.id
        logger.info(f"Created chat with ID: {new_chat.id} for user: {request.user_id}")

    except Exception as e:
        logger.exception(
            f"Error creating a session for user:{request.user_id}, error : {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error while creating a session",
        )

    return StartChatResponse(**session_data)


@chat_router.post("/query", status_code=status.HTTP_200_OK)
def query(
    request: ChatQueryRequest,
    db: Session = Depends(db_client.get_db),
    chat_service: ChatService = Depends(
        lambda: get_chat_service(
            llm_client_instance=llm_client, session_store=session_store
        )
    ),
) -> dict:
    """Process a chat query and generate a retrieval plan with documents

    Queries are scoped to documents associated with the specified chat_id.
    The query and answer are stored in the chat's history.
    """
    try:
        # Verify session exists
        session_data = session_store.get_session(request.session_id)
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid session or session expired",
            )

        # Get chat and its associated documents
        chat_repo = ChatRepository(db)
        chat = chat_repo.get_chat_by_id(request.chat_id)
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chat with ID {request.chat_id} not found",
            )

        # Get document filenames associated with this chat
        document_filenames = [doc.filename for doc in chat.documents]

        if not document_filenames:
            logger.warning(f"No documents associated with chat {request.chat_id}")
            return {
                "query": request.query,
                "answer": "No documents have been uploaded to this chat yet. Please upload documents first.",
                "sources": [],
                "num_sources": 0,
            }

        logger.info(
            f"Processing query for chat {request.chat_id} with {len(document_filenames)} documents"
        )

        # Delegate business logic to service layer (with document filtering)
        result = chat_service.process_query(
            session_id=request.session_id,
            query=request.query,
            document_filenames=document_filenames,
        )

        # Store query and answer in chat history
        try:
            chat_repo.update_chat_history(
                chat_id=request.chat_id,
                query=request.query,
                answer=result.get("answer", ""),
            )
            logger.info(
                f"Stored query/answer in chat history for chat {request.chat_id}"
            )
        except Exception as history_error:
            logger.error(f"Failed to update chat history: {history_error}")
            # Don't fail the request if history update fails

        return result

    except HTTPException:
        raise
    except ValueError as ve:
        # Handle validation errors (invalid session, empty query, etc.)
        logger.error(f"Validation error: {str(ve)}")
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
                if "session" in str(ve).lower() or "chat" in str(ve).lower()
                else status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=str(ve),
        )
    except Exception as e:
        logger.exception(f"Error processing query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process query",
        )
