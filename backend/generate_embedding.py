import ollama
from typing import List
from config import Settings

class GenerateEmbedding:
    def __init__(self, model_name: str = Settings().EMBEDDING_MODEL):
        self.model_name = model_name

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts using the Ollama API."""
        if not texts:
            return []
        response = ollama.embed(model=self.model_name, input=texts)
        return response['embeddings']
    
    def embed_query(self, query: str) -> List[float]:
        """Generate an embedding for a single query string."""
        response = ollama.embed(model=self.model_name, input=query)
        return response['embeddings'][0]