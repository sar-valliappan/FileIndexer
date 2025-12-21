from math import ceil
import os
from pathlib import Path
from typing import Optional
import pypdf
from docx import Document
from config import Settings

class FileProcessor:
    """Class to handle file processing and text extraction."""
    settings = Settings()

    @staticmethod
    def extract_text_from_pdf(file_path: str) -> Optional[str]:
        """Extract text from a PDF file."""
        try:
            with open(file_path, 'rb') as file:
                reader = pypdf.PdfReader(file)
                text = []
                for page in reader.pages:
                    text.append(page.extract_text())
                return "\n".join(text)
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return None

    @staticmethod 
    def extract_text_from_docx(file_path: str) -> Optional[str]:
        """Extract text from a DOCX file."""
        try:
            doc = Document(file_path)
            text = []
            for paragraph in doc.paragraphs:
                text.append(paragraph.text)
            return "\n".join(text)
        except Exception as e:
            print(f"Error extracting text from DOCX: {e}")
            return None
        
    @staticmethod
    def extract_text_from_txt(file_path: str) -> Optional[str]:
        """Extract text from a TXT file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"Error extracting text from TXT: {e}")
            return None

    @staticmethod
    def process_file(file_path: str) -> Optional[str]:
        """Process a file and extract its text based on the file type."""
        extension = Path(file_path).suffix.lower()
        if extension == '.pdf':
            return FileProcessor.extract_text_from_pdf(file_path)
        elif extension == '.docx':
            return FileProcessor.extract_text_from_docx(file_path)
        elif extension == '.txt':
            return FileProcessor.extract_text_from_txt(file_path)
        else:
            print(f"Unsupported file type: {extension}")
            return None
    
    @staticmethod
    def chunk_text(text: str, chunk_size: int = settings.CHUNK_SIZE, overlap: int = settings.CHUNK_OVERLAP) -> list:
        """Chunk text into smaller pieces."""
        chunks = []
        start = 0
        text_length = len(text)

        if (text_length <= chunk_size):
            return [text]

        num_chunks = ceil((text_length - overlap) / (chunk_size - overlap))
        chunk_size = ceil(text_length / num_chunks) + overlap

        
        while start < text_length:
            end = min(start + chunk_size, text_length)
            chunks.append(text[start:end])
            start += chunk_size - overlap
            
        return chunks