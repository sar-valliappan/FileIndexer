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