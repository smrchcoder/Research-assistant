from fastapi import APIRouter, HTTPException, status
from ..schema import QueryResponse, QueryRequest,SourceInfo
from ..services import QueryService, QueryPromptTemplate
import logging
from ..memory.session_store import session_store

logger = logging.getLogger(__name__)

query_router = APIRouter()



@query_router.post("/query", response_model=QueryResponse)
async def receive_query(request: QueryRequest) -> QueryResponse:
    """
    Process a user query using RAG (Retrieval-Augmented Generation)
    
    Args:
        request: Query request with question and parameters (validated by QueryRequest model)
        
    Returns:
        QueryResponse: Generated answer with source citations (validated by response_model)
    """
    try:
        session_data = session_store.get_session(request.session_id)
        if not session_data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Invalid session or Session Expired",
                )
        logger.info(f"Processing query: {request.query[:100]}...")
        logger.info(f"Request params - top_k: {request.top_k}, temperature: {request.temperature}, model: {request.model}")
        
        # Step 1 & 2: Initialize service and retrieve similar documents
        query_service = QueryService(query=request.query)
        search_results = query_service.retrieve_similarities()
        
        # Extract documents and metadata from results
        # ChromaDB returns nested lists: {'documents': [[doc1, doc2, ...]], 'metadatas': [[meta1, meta2, ...]]}
        documents = search_results.get('documents', [[]])[0][:request.top_k]
        metadatas = search_results.get('metadatas', [[]])[0][:request.top_k]
        
        if not documents:
            logger.warning("No relevant documents found")

            return QueryResponse(
                query_id=query_service.query_id,
                query=request.query,
                answer="I couldn't find any relevant information in the database to answer your question.",
                sources=[],
                num_sources=0
            )
        
        # Step 3: Format context using prompt template
        prompt_template = QueryPromptTemplate()
        formatted_context = prompt_template.generate_context(documents, metadatas)
        messages = prompt_template.generate_prompt(formatted_context, request.query)
        
        # Step 4: Generate answer
        answer = query_service.generate_answer(
            messages=messages,
            model=request.model,
            temperature=request.temperature
        )
        
        sources = [
            SourceInfo(
                document_id=meta.get('document_id', 'Unknown'),
                page_number=meta.get('page_number', 'Unknown'),
                chunk_id=meta.get('chunk_id', 'Unknown')
            )
            for meta in metadatas
        ]
        
        response = QueryResponse(
            query_id=query_service.query_id,
            query=request.query,
            answer=answer,
            sources=sources,
            num_sources=len(sources)
        )
        session_store.add_message(session_id=request.session_id, question=request.query, answer=answer)
        
        logger.info(f"Successfully processed query: {query_service.query_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your query. Please try again."
        )
