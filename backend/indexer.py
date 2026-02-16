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
            file_paths = [p.resolve() for p in file_paths]
            indexed_files = self.get_indexed_files()
            current_files = {str(p): p for p in file_paths}

            for indexed_path in indexed_files:
                if indexed_path not in current_files:
                    self.collection.delete(
                        where={"file_path": {"$eq": indexed_path}}
                    )

            for i, file_path in enumerate(file_paths):
                if self.progress_callback:
                    self.progress_callback(f"Indexing {file_path}", i, len(file_paths))

                file_text = self.file_processor.process_file(file_path)
                if not file_text or not file_text.strip():
                    continue

                file_hash = self.get_file_hash(file_path)
                path_str = str(file_path)

                if indexed_files.get(path_str) == file_hash:
                    continue

                if path_str in indexed_files:
                    self.collection.delete(
                        where={"file_path": {"$eq": path_str}}
                    )

                chunks = self.file_processor.chunk_text(file_text)
                embeddings = self.generate_embedding.generate_embeddings(chunks)

                modified_time = datetime.fromtimestamp(file_path.stat().st_mtime)

                metadatas = []
                ids = []

                for chunk_idx, chunk in enumerate(chunks):
                    metadatas.append({
                        "file_name": file_path.name,
                        "file_extension": file_path.suffix,
                        "file_path": path_str,
                        "file_hash": file_hash,
                        "file_size": file_path.stat().st_size,
                        "modified_time": modified_time.isoformat(),
                        "total_chunks": len(chunks),
                        "chunk_index": chunk_idx
                    })
                    ids.append(f"{path_str}::{chunk_idx}")

                self.collection.add(
                    documents=chunks,
                    metadatas=metadatas,
                    embeddings=embeddings,
                    ids=ids
                )

                print(f"Indexed {file_path} ({len(chunks)} chunks)")

        except Exception as e:
            print(f"Error indexing files: {e}")
    
    def index_directory(self, directory_path: str):
        """Scan and index all files in a directory."""
        file_paths = self.scan_directory(directory_path)
        self.index_files(file_paths)

    def search(self, query: str, n_results: int = settings.SEARCH_RESULT_COUNT) -> List[Dict]:
        """Search with hybrid scoring: semantic + keyword + recency"""
        try:
            query_embedding = self.generate_embedding.embed_query(query)
            query_lower = query.lower()
            query_terms = set(query_lower.split())
            
            # Retrieve more chunks initially for better file-level aggregation
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(n_results * 10, 100),  # Cap at 100 to avoid slowdown
                include=["documents", "metadatas", "distances"]
            )
            
            file_results = {}
            
            if results['ids']:
                for i in range(len(results['ids'][0])):
                    file_path = results['metadatas'][0][i]['file_path']
                    chunk_text = results['documents'][0][i]
                    distance = results['distances'][0][i]
                    similarity = 1 - distance
                    metadata = results['metadatas'][0][i]
                    
                    # Calculate keyword overlap score
                    chunk_lower = chunk_text.lower()
                    keyword_score = sum(1 for term in query_terms if term in chunk_lower) / len(query_terms)
                    
                    # Check for exact phrase match
                    exact_match = query_lower in chunk_lower
                    
                    if file_path not in file_results:
                        file_results[file_path] = {
                            'file_path': file_path,
                            'chunks': [],
                            'similarities': [],
                            'keyword_scores': [],
                            'has_exact_match': False,
                            'best_chunk': chunk_text,
                            'best_similarity': similarity,
                            'metadata': metadata
                        }
                    
                    file_results[file_path]['chunks'].append(chunk_text)
                    file_results[file_path]['similarities'].append(similarity)
                    file_results[file_path]['keyword_scores'].append(keyword_score)
                    
                    if exact_match:
                        file_results[file_path]['has_exact_match'] = True
                    
                    # Track best chunk for preview
                    if similarity > file_results[file_path]['best_similarity']:
                        file_results[file_path]['best_chunk'] = chunk_text
                        file_results[file_path]['best_similarity'] = similarity
            
            aggregated_results = []
            now = datetime.now()
            
            for file_path, data in file_results.items():
                similarities = sorted(data['similarities'], reverse=True)
                keyword_scores = sorted(data['keyword_scores'], reverse=True)
                
                # 1. Semantic score: Weighted average favoring top chunks
                k = min(3, len(similarities))
                weights = [0.5, 0.3, 0.2][:k]  # Top chunk gets 50%, second 30%, third 20%
                semantic_score = sum(sim * w for sim, w in zip(similarities[:k], weights)) / sum(weights)
                
                # 2. Keyword score: Average of top-k keyword matches
                keyword_score = sum(keyword_scores[:k]) / k if k > 0 else 0
                
                # 3. Coverage score: Reward files with multiple relevant chunks
                coverage_ratio = min(len([s for s in similarities if s > 0.6]), 5) / 5
                coverage_score = coverage_ratio * 0.15
                
                # 4. Recency score: Boost recently modified files
                modified_time = datetime.fromisoformat(data['metadata']['modified_time'])
                days_old = (now - modified_time).days
                recency_score = max(0, (365 - days_old) / 365) * 0.1  # Max 10% boost for files <1 year old
                
                # 5. Exact match bonus
                exact_match_bonus = 0.15 if data['has_exact_match'] else 0
                
                # Combined score
                final_score = (
                    semantic_score * 0.6 +      # 60% semantic
                    keyword_score * 0.25 +      # 25% keyword
                    coverage_score +             # 15% coverage
                    recency_score +              # 10% recency
                    exact_match_bonus            # 15% exact match bonus
                )
                
                aggregated_results.append({
                    'file_path': file_path,
                    'chunk_text': data['best_chunk'][:300] + "..." if len(data['best_chunk']) > 300 else data['best_chunk'],
                    'similarity': final_score,
                    'distance': 1 - final_score,
                    'chunks': data['chunks'],
                    'total_chunks': len(data['chunks']),
                    'metadata': data['metadata'],
                    # Debug scores (optional, remove in production)
                    'scores': {
                        'semantic': semantic_score,
                        'keyword': keyword_score,
                        'coverage': coverage_score,
                        'recency': recency_score,
                        'exact_match': exact_match_bonus
                    }
                })
            
            aggregated_results.sort(key=lambda x: x['similarity'], reverse=True)
            
            return aggregated_results[:n_results]
            
        except Exception as e:
            print(f"Search error: {e}")
            return []
