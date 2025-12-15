import ollama
from typing import List

class GenerateEmbedding:
    def __init__(self, model_name: str = "nomic-embed-text"):
        self.model_name = model_name

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts using the Ollama API."""
        embeddingsList = []
        for text in texts:
            response = ollama.embed(model=self.model_name, input=text)
            embeddingsList.append(response['embeddings'][0])
        return embeddingsList
    
    def embed_query(self, query: str) -> List[float]:
        """Generate an embedding for a single query string."""
        response = ollama.embed(model=self.model_name, input=query)
        return response['embeddings'][0]