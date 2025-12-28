from langchain_text_splitters import RecursiveCharacterTextSplitter
import uuid
from typing import Dict, List, Any


class TextChunker:
    def __init__(self, chunk_size=1000, overlap_size=200):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap_size,
            length_function=len,
            is_separator_regex=False,
        )

    def generate_chunks(
        self, document_id: str, document: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Generate chunks from document pages with proper position tracking

        Args:
            document_id: Unique identifier for the document (filename)
            document: Dict of {page_key: page_content}

        Returns:
            List of chunk dictionaries with metadata
        """
        chunks = []
        global_position = 0  # Track position across entire document

        # Sort pages to ensure proper order (page_1, page_2, etc.)
        sorted_pages = sorted(
            document.items(),
            key=lambda x: int(x[0].split("_")[1]) if x[0].startswith("page_") else 0,
        )

        for page_key, page_content in sorted_pages:
            # Skip empty pages
            if not page_content:
                continue

            # Extract page number
            page_number = (
                int(page_key.split("_")[1]) if page_key.startswith("page_") else 0
            )

            # Split page content into chunks
            chunked_texts = self.text_splitter.split_text(page_content)

            for chunk_text in chunked_texts:
                chunk_data = {
                    "chunk_id": str(uuid.uuid4()),
                    "document_id": document_id,
                    "page_number": page_number,
                    "text": chunk_text,
                    "char_count": len(chunk_text),
                    "start_position": global_position,
                    "end_position": global_position + len(chunk_text),
                }
                chunks.append(chunk_data)

                # Update global position (accounting for overlap)
                # Move forward by chunk size minus overlap
                global_position += len(chunk_text) - self.text_splitter._chunk_overlap

        return chunks
