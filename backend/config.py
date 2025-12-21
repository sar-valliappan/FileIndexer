import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Paths
    PROJECT_ROOT: Path = Path(__file__).parent.parent
    DATA_DIR: Path = PROJECT_ROOT / "data"
    CHROMA_DB_DIR: Path = DATA_DIR / "chroma_db"
    
    # Ollama settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    EMBEDDING_MODEL: str = "nomic-embed-text"
    
    # Indexing settings
    CHUNK_SIZE: int = 1000  # characters
    CHUNK_OVERLAP: int = 200
    MAX_FILE_SIZE_MB: int = 100

    # Valid file extensions for indexing
    VALID_FILE_EXTENSIONS: list[str] = [
        ".txt", ".pdf", ".docx"
    ]

    # Query settings
    SEARCH_RESULT_COUNT: int = 5
    
    # Collection name in ChromaDB
    COLLECTION_NAME: str = "file_embeddings"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create necessary directories
        self.DATA_DIR.mkdir(exist_ok=True)
        self.CHROMA_DB_DIR.mkdir(exist_ok=True)

settings = Settings()