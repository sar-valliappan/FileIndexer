import hashlib
from pathlib import Path
from typing import Callable

import chromadb
from chromadb.config import Settings as ChromaSettings

from config import Settings
from file_processor import FileProcessor
from generate_embedding import GenerateEmbedding

class Indexer:
    """Class to handle indexing of files into a ChromaDB collection."""
    settings = Settings()

    def __init__(self, progress_callback: Callable[[str, int, int], None] = None):
        self.generate_embedding = GenerateEmbedding()
        self.file_processor = FileProcessor()
        self.progress_callback = progress_callback
        
        self.client = chromadb.PersistentClient(
            path=str(self.settings.CHROMA_DB_DIR),
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        self.collection = self.client.get_or_create_collection(
            name=self.settings.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
    
    def scan_directory(self, directory_path: str):
        """Scan a directory for files and index them."""
        directory = Path(directory_path)
        files = list(directory.rglob('*.*'))
        
        return files
    
    def get_file_hash(self, file_path: Path):
        with open(file_path, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        
        return file_hash            