import os
from pathlib import Path
from typing import Optional
import pypdf
from docx import Document

class FileProcessor:

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