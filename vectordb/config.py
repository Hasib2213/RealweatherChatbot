import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Tuple, Optional
import pickle
from pathlib import Path

class VectorDBConfig:
    """Configuration for FAISS Vector Database"""
    
    def __init__(self):
        self.enabled = os.getenv("VECTORDB_ENABLED", "false").lower() == "true"
        self.index_path = os.getenv("FAISS_INDEX_PATH", "./data/faiss_index")
        self.embedding_model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.dimension = 384  # Dimension for all-MiniLM-L6-v2
        
        # Create directory if it doesn't exist
        Path(self.index_path).parent.mkdir(parents=True, exist_ok=True)

vectordb_config = VectorDBConfig()


class FAISSVectorStore:
    """FAISS Vector Store for storing and retrieving weather conversations"""
    
    def __init__(self, config: VectorDBConfig):
        self.config = config
        self.model = SentenceTransformer(config.embedding_model_name)
        self.index = None
        self.documents = []
        self.metadata = []
        
        # Initialize or load index
        self._initialize_index()
    
    def _initialize_index(self):
        """Initialize or load existing FAISS index"""
        index_file = f"{self.config.index_path}/index.faiss"
        docs_file = f"{self.config.index_path}/documents.pkl"
        meta_file = f"{self.config.index_path}/metadata.pkl"
        
        if os.path.exists(index_file):
            # Load existing index
            self.index = faiss.read_index(index_file)
            
            if os.path.exists(docs_file):
                with open(docs_file, 'rb') as f:
                    self.documents = pickle.load(f)
            
            if os.path.exists(meta_file):
                with open(meta_file, 'rb') as f:
                    self.metadata = pickle.load(f)
        else:
            # Create new index
            self.index = faiss.IndexFlatL2(self.config.dimension)
    
    def add_documents(self, texts: List[str], metadata_list: List[dict] = None):
        """Add documents to the vector store"""
        if not texts:
            return
        
        # Generate embeddings
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        
        # Add to FAISS index
        self.index.add(embeddings.astype('float32'))
        
        # Store documents and metadata
        self.documents.extend(texts)
        if metadata_list:
            self.metadata.extend(metadata_list)
        else:
            self.metadata.extend([{} for _ in texts])
        
        # Save index
        self._save_index()
    
    def search(self, query: str, k: int = 5) -> List[Tuple[str, float, dict]]:
        """Search for similar documents"""
        if self.index.ntotal == 0:
            return []
        
        # Generate query embedding
        query_embedding = self.model.encode([query], convert_to_numpy=True)
        
        # Search
        distances, indices = self.index.search(query_embedding.astype('float32'), k)
        
        # Format results
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.documents):
                results.append((
                    self.documents[idx],
                    float(distance),
                    self.metadata[idx] if idx < len(self.metadata) else {}
                ))
        
        return results
    
    def _save_index(self):
        """Save FAISS index and documents to disk"""
        index_file = f"{self.config.index_path}/index.faiss"
        docs_file = f"{self.config.index_path}/documents.pkl"
        meta_file = f"{self.config.index_path}/metadata.pkl"
        
        # Save FAISS index
        faiss.write_index(self.index, index_file)
        
        # Save documents
        with open(docs_file, 'wb') as f:
            pickle.dump(self.documents, f)
        
        # Save metadata
        with open(meta_file, 'wb') as f:
            pickle.dump(self.metadata, f)
    
    def get_stats(self) -> dict:
        """Get statistics about the vector store"""
        return {
            "total_documents": self.index.ntotal if self.index else 0,
            "dimension": self.config.dimension,
            "model": self.config.embedding_model_name,
            "index_type": "FAISS IndexFlatL2"
        }
    
    def clear(self):
        """Clear all documents from the vector store"""
        self.index = faiss.IndexFlatL2(self.config.dimension)
        self.documents = []
        self.metadata = []
        self._save_index()


# Global vector store instance
vector_store = FAISSVectorStore(vectordb_config) if vectordb_config.enabled else None