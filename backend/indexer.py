import hashlib
from pathlib import Path
from typing import List, Dict, Callable
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
        files = []
        for ext in self.settings.VALID_FILE_EXTENSIONS:
            files.extend(directory.glob(f'*{ext}'))

        print(f"Found {len(files)} files to index.")
        return files
    
    def get_file_hash(self, file_path: Path):
        with open(file_path, 'rb') as f:
            file_hash = hashlib.sha256(self.file_processor.process_file(file_path).encode()).hexdigest()
        
        return file_hash
    
    def get_indexed_files(self) -> Dict[str, str]:
        """Return {file_path: file_hash} for already-indexed files."""
        results = self.collection.get(include=["metadatas"])
        
        indexed = {}
        for md in results.get("metadatas", []):
            indexed[md["file_path"]] = md["file_hash"]
        
        return indexed

    def index_files(self, file_paths: list[Path]):
        try: 
            indexed_files = self.get_indexed_files()
            files = {str(p): p for p in file_paths}

            for indexed_path in indexed_files:
                if indexed_path not in files:
                    self.collection.delete(
                        where={"file_path": {"$eq": indexed_path}}
                    )

            for i, file_path in enumerate(file_paths):
                if self.progress_callback:
                    self.progress_callback(f"Indexing {file_path}", i, len(file_paths))
                
                file_text = self.file_processor.process_file(file_path)
                file_hash = self.get_file_hash(file_path)

                if (file_text is None) or (len(file_text.strip()) == 0):
                    continue

                if str(file_path) in indexed_files and indexed_files[str(file_path)] == file_hash:
                    continue

                if str(file_path) in indexed_files:
                    self.collection.delete(
                        where={"file_path": {"$eq": file_path}}
                    )

                chunks = self.file_processor.chunk_text(file_text)
                embeddings = self.generate_embedding.generate_embeddings(chunks)       
                
                file_hash = self.get_file_hash(file_path)
                modified_time = datetime.fromtimestamp(file_path.stat().st_mtime)

                metadatas = []
                ids = []
                for chunk_idx in range(len(chunks)):
                    metadatas.append({
                        "file_name": file_path.name,
                        "file_extension": file_path.suffix,
                        "file_path": str(file_path),
                        "file_hash": file_hash,
                        "file_size": file_path.stat().st_size,
                        "modified_time": modified_time.isoformat(),
                        "total_chunks": len(chunks),
                        "chunk_index": chunk_idx
                    }) 
                    ids.append(f"{file_path}_{chunk_idx}")

                self.collection.add(
                    documents=chunks,
                    metadatas=metadatas,
                    embeddings=embeddings,
                    ids=ids
                )
                print(f"Indexed {file_path} with {len(chunks)} chunks.")

        except Exception as e:
            print(f"Error indexing files: {e}")
    
    def index_directory(self, directory_path: str):
        """Scan and index all files in a directory."""
        file_paths = self.scan_directory(directory_path)
        self.index_files(file_paths)

    def search(self, query: str, n_results: int = settings.SEARCH_RESULT_COUNT) -> List[Dict]:
        """Search for files matching the query with file-level aggregation"""
        try:
            query_embedding = self.generate_embedding.embed_query(query)
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results * 5,
                include=["documents", "metadatas", "distances"]
            )
            
            file_results = {}
            
            if results['ids']:
                for i in range(len(results['ids'][0])):
                    file_path = results['metadatas'][0][i]['file_path']
                    chunk_text = results['documents'][0][i]
                    distance = results['distances'][0][i] if 'distances' in results else RuntimeError("Chroma query did not return distances")
                    similarity = 1 - distance
                    metadata = results['metadatas'][0][i]
                    
                    if file_path not in file_results:
                        file_results[file_path] = {
                            'file_path': file_path,
                            'chunks': [],
                            'similarities': [],
                            'best_chunk': chunk_text,
                            'best_similarity': similarity,
                            'metadata': metadata
                        }
                    
                    file_results[file_path]['chunks'].append(chunk_text)
                    file_results[file_path]['similarities'].append(similarity)
                    
                    if similarity > file_results[file_path]['best_similarity']:
                        file_results[file_path]['best_chunk'] = chunk_text
                        file_results[file_path]['best_similarity'] = similarity
            
            aggregated_results = []
            for file_path, data in file_results.items():
                similarities = data['similarities']
                similarities.sort(reverse=True)
                k = min(3, len(similarities))
                best_similarity = sum(similarities[:k]) / k

                aggregated_results.append({
                    'file_path': file_path,
                    'chunk_text': data['best_chunk'][:300] + "...",
                    'similarity': best_similarity,
                    'distance': 1 - best_similarity,
                    'chunks': data['chunks'],
                    'total_chunks': len(data['chunks']),
                    'metadata': data['metadata']
                })
            
            aggregated_results.sort(key=lambda x: x['similarity'], reverse=True)
            
            return aggregated_results[:n_results]
            
        except Exception as e:
            print(f"Search error: {e}")
            return []
