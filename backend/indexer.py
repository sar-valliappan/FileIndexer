import hashlib
from pathlib import Path
from typing import Callable
from datetime import datetime

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

    def index_files(self, file_paths: list[Path]):
        try: 
            for i, file_path in enumerate(file_paths):
                if self.progress_callback:
                    self.progress_callback(f"Indexing {file_path}", i, len(file_paths))
                
                file_text = self.file_processor.process_file(file_path)
                chunks = self.file_processor.chunk_text(file_text)
                embeddings = self.generate_embedding.generate_embeddings(chunks)            
                
                file_hash = self.get_file_hash(file_path)
                modified_time = datetime.fromtimestamp(file_path.stat().st_mtime)

                metadatas = [{
                    "file_name": file_path.name,
                    "file_extension": file_path.suffix,
                    "file_path": str(file_path),
                    "file_hash": file_hash,
                    "file_size": file_path.stat().st_size,
                    "modified_time": modified_time.isoformat(),
                    "total_chunks": len(chunks),
                    "chunk_index": i
                } for i in range(len(chunks))]

                ids = [f"{file_path}_{i}" for i in range(len(chunks))]

                self.collection.add(
                    documents=chunks,
                    metadatas=metadatas,
                    embeddings=embeddings,
                    ids=ids
                )

        except Exception as e:
            print(f"Error indexing files: {e}")
    
    def index_directory(self, directory_path: str):
        """Scan and index all files in a directory."""
        file_paths = self.scan_directory(directory_path)
        self.index_files(file_paths)