from fastapi import APIRouter, HTTPException, status, Depends
from ..models import StartChatRequest, StartChatResponse, ChatQueryRequest
from ..memory.session_store import session_store
import logging
from ..services.chat_service import ChatService, get_chat_service
from ..llm import llm_client

logger = logging.getLogger(__name__)

chat_router = APIRouter()


@chat_router.post(
    "/start", response_model=StartChatResponse, status_code=status.HTTP_201_CREATED
)
def start_chat(request: StartChatRequest) -> StartChatResponse:
    """Create a new chat session for a user

    This endpoint creates a new session in Redis that will store
    conversation history for 1 hour (configurable via SESSION_TTL_SECONDS).
    """
    try:
        logger.info(f"Starting chat session for user: {request.user_id}")

        session_data = session_store.create_session(request.user_id)

        if not session_data:
            logger.error(f"Failed to create session for user: {request.user_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create chat session",
            )
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
    chat_service: ChatService = Depends(
        lambda: get_chat_service(
            llm_client_instance=llm_client, session_store=session_store
        )
    ),
) -> dict:
    """Process a chat query and generate a retrieval plan with documents"""
    try:
        # Delegate business logic to service layer
        result = chat_service.process_query(
            session_id=request.session_id, query=request.query
        )

        return result

    except ValueError as ve:
        # Handle validation errors (invalid session, empty query, etc.)
        logger.error(f"Validation error: {str(ve)}")
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
                if "session" in str(ve).lower()
                else status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
        )
    except Exception as e:
        logger.exception(f"Error processing query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process query",
        )
