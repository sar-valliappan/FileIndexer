import os
from pathlib import Path
from typing import Optional
import pypdf
from docx import Document

class FileProcessor:

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