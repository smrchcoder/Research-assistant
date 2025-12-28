from fastapi import UploadFile
from datetime import datetime
from typing import Dict, Set, Tuple
import os
import fitz  # PyMuPDF
import re
from collections import Counter
from ..core import settings
from ..exceptions import FileProcessingError
import logging

logger = logging.getLogger(__name__)


class FileService:
    """Service for handling PDF file uploads and text extraction"""

    def __init__(self):
        self.upload_dir = settings.upload_directory

    async def upload_file(self, pdf_file: UploadFile) -> Dict[str, str]:
        """
        Upload PDF file and extract text
        
        Args:
            pdf_file: The uploaded PDF file
            
        Returns:
            Dict of {page_key: cleaned_text}
            
        Raises:
            FileProcessingError: If file processing fails
        """
        if not pdf_file.filename.lower().endswith(".pdf"):
            raise FileProcessingError(pdf_file.filename, "Only PDF files are allowed")

        try:
            current_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            file_path = os.path.join(
                self.upload_dir, f"{pdf_file.filename}_{current_timestamp}"
            )

            # Ensure upload directory exists
            os.makedirs(self.upload_dir, exist_ok=True)

            with open(file_path, "wb") as f:
                content = await pdf_file.read()
                f.write(content)

            logger.info(f"File saved to {file_path}")
            
            return self.extract_text_from_document(file_path=file_path)
        
        except FileProcessingError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            # Wrap unexpected errors in FileProcessingError
            logger.error(f"Unexpected error processing file '{pdf_file.filename}': {e}")
            raise FileProcessingError(pdf_file.filename, str(e))

    def extract_text_from_document(self, file_path: str) -> Dict[str, str]:
        """
        Extract text from PDF using PyMuPDF (fitz) for better multi-column handling.

        PyMuPDF provides superior text extraction for academic papers and
        multi-column documents by properly detecting reading order and
        maintaining word spacing.

        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dict of {page_key: cleaned_text}
            
        Raises:
            FileProcessingError: If text extraction fails
        """
        try:
            pages = {}
            # Open PDF with PyMuPDF
            pdf_doc = fitz.open(file_path)

            if pdf_doc.page_count == 0:
                raise FileProcessingError(file_path, "PDF has no pages")

            for page_num in range(pdf_doc.page_count):
                page = pdf_doc[page_num]
                page_key = f"page_{page_num + 1}"

                # Extract text with PyMuPDF
                # flags parameter controls text extraction behavior:
                # 0: default (good for multi-column)
                # fitz.TEXTFLAGS_TEXT: preserve text layout
                # fitz.TEXTFLAGS_HTML: HTML output
                # fitz.TEXTFLAGS_DICT: structured output
                # fitz.TEXTFLAGS_WORDS: word-level extraction
                extracted_page_text = page.get_text(
                    "text",  # Plain text format
                    flags=fitz.TEXTFLAGS_WORDS,  # Use word-level extraction for better spacing
                )

                if not extracted_page_text or extracted_page_text.strip() == "":
                    pages[page_key] = None
                    continue

                pages[page_key] = extracted_page_text

            # Close the PDF document
            pdf_doc.close()

            # Detect and remove headers/footers
            header, footer = self._detect_headers_and_footers(pages)

            # Clean each page
            for page_key, page_info in pages.items():
                if not page_info:
                    continue
                pages[page_key] = self.clean_extracted_page_info(
                    page_info, header=header, footer=footer
                )

            return pages

        except FileProcessingError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            # Wrap unexpected errors
            logger.error(f"Error extracting text from PDF '{file_path}': {e}")
            raise FileProcessingError(file_path, f"Text extraction failed: {str(e)}")

    def _detect_headers_and_footers(
        self, pages: Dict[str, str]
    ) -> Tuple[Set[str], Set[str]]:
        """
        Detect common headers and footers across pages

        Returns:
            Tuple of (header_set, footer_set)
        """
        header_candidates = []
        footer_candidates = []

        for page in pages.values():
            if not page:  # Skip empty pages
                continue

            lines = [line.strip() for line in page.splitlines() if line.strip()]

            if len(lines) > 0:
                header_candidates.append(lines[0])
            if len(lines) > 1:
                footer_candidates.append(lines[-1])

        header_counter = Counter(header_candidates)
        footer_counter = Counter(footer_candidates)

        # Consider a line as header/footer if it appears in >50% of pages
        threshold = 0.5
        header = {
            line
            for line, count in header_counter.items()
            if count > threshold * len(header_candidates)
        }
        footer = {
            line
            for line, count in footer_counter.items()
            if count > threshold * len(footer_candidates)
        }

        return header, footer

    def clean_extracted_page_info(
        self, page_info: str, header: Set[str], footer: Set[str]
    ) -> str:
        """
        Clean page text by removing headers, footers, and normalizing whitespace.

        Optimized for PyMuPDF output which generally has better word spacing
        but may still have some formatting issues from complex layouts.
        """
        page_lines = []
        for line in page_info.splitlines():
            line = line.strip()
            if not line:
                continue
            if line in header or line in footer:
                continue
            page_lines.append(line)

        page_info = "\n".join(page_lines)

        # Remove hyphenation at line breaks (replace with nothing to join words)
        page_info = re.sub(r"-\n", "", page_info)

        # Replace single newlines with spaces (preserve paragraph breaks)
        page_info = re.sub(r"(?<!\n)\n(?!\n)", " ", page_info)

        # Fix concatenated words: add space between lowercase-to-uppercase transitions
        # PyMuPDF generally handles spacing better, but this helps with edge cases
        page_info = re.sub(r"([a-z])([A-Z][a-z])", r"\1 \2", page_info)

        # Fix cases where periods are stuck to next word: "end.Next" -> "end. Next"
        page_info = re.sub(r"([.!?])([A-Z][a-z])", r"\1 \2", page_info)

        # Normalize excessive newlines (3+ becomes 2 for paragraph breaks)
        page_info = re.sub(r"\n{3,}", "\n\n", page_info)

        # Normalize whitespace (multiple spaces/tabs become single space)
        page_info = re.sub(r"[ \t]+", " ", page_info)

        # Clean up any remaining extra spaces around newlines
        page_info = re.sub(r" *\n *", "\n", page_info)

        return page_info.strip()
