from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class QueryPromptTemplate:
    """Template for generating prompts with retrieved context for RAG"""
    
    SYSTEM_PROMPT = """You are a helpful and accurate research assistant. Your task is to answer questions based ONLY on the provided document context.

Key principles:
- Use only information from the provided context
- Cite sources with document name and page number
- If the answer is not in the context, explicitly state that
- Provide clear, well-structured answers
- Be factual and avoid speculation"""

    def generate_context(self, documents: List[str], metadatas: List[Dict[str, Any]]) -> str:
        """
        Format retrieved documents into structured context
        
        Args:
            documents: List of document text chunks
            metadatas: List of metadata dictionaries for each document
            
        Returns:
            Formatted context string
        """
        if not documents or not metadatas:
            logger.warning("No documents or metadata provided for context generation")
            return "No relevant context found."
        
        context_parts = []
        for idx, (document, metadata) in enumerate(zip(documents, metadatas), 1):
            doc_id = metadata.get('document_id', 'Unknown')
            page_num = metadata.get('page_number', 'Unknown')
            chunk_id = metadata.get('chunk_id', 'Unknown')
            
            context_part = (
                f"[Source {idx}]\n"
                f"Document: {doc_id}\n"
                f"Page: {page_num}\n"
                f"Content: {document}\n"
            )
            context_parts.append(context_part)
        
        formatted_context = "\n".join(context_parts)
        logger.info(f"Generated context from {len(documents)} documents")
        return formatted_context

    def generate_prompt(self, context: str, query: str) -> List[Dict[str, str]]:
        """
        Generate complete prompt messages for OpenAI chat API
        
        Args:
            context: Formatted context from retrieved documents
            query: User's question
            
        Returns:
            List of message dictionaries for OpenAI API
        """
        user_prompt = f"""Based on the following context, please answer the question.

Context:
{context}

---

Question: {query}

Answer (with citations):"""
        
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
        
        logger.info(f"Generated prompt for query: {query[:50]}...")
        return messages