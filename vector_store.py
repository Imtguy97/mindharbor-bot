"""
Lightweight in-memory vector store for Python 3.14 compatibility.
Replaces Chroma to avoid pydantic.v1 incompatibility issues.
"""
import json
import pickle
import sqlite3
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from sentence_transformers import SentenceTransformer
import numpy as np

class SimpleVectorStore:
    """In-memory vector store with SQLite persistence."""
    
    def __init__(self, db_path: Optional[str] = None, model_name: str = "all-MiniLM-L6-v2"):
        # Default to putting db_path in same directory as src
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), "vector_store.db")
        
        # Ensure db_path is absolute
        if not os.path.isabs(db_path):
            db_path = os.path.abspath(db_path)
        
        # Ensure directory exists
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        self.db_path = db_path
        self.model = SentenceTransformer(model_name)
        self.vectors: Dict[str, np.ndarray] = {}
        self.texts: Dict[str, str] = {}
        self.conn = None
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database for persistence."""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vectors (
                id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                vector BLOB NOT NULL
            )
        """)
        self.conn.commit()
    
    def add_texts(self, texts: List[str], ids: Optional[List[str]] = None) -> List[str]:
        """Add texts to the vector store."""
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(texts))]
        
        # Embed texts
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        
        cursor = self.conn.cursor()
        for doc_id, text, embedding in zip(ids, texts, embeddings):
            vector_bytes = pickle.dumps(embedding)
            cursor.execute(
                "INSERT OR REPLACE INTO vectors (id, text, vector) VALUES (?, ?, ?)",
                (doc_id, text, vector_bytes)
            )
            self.vectors[doc_id] = embedding
            self.texts[doc_id] = text
        
        self.conn.commit()
        return ids
    
    def similarity_search(self, query: str, k: int = 3) -> List[Tuple[str, float]]:
        """Search for similar texts."""
        query_embedding = self.model.encode(query, convert_to_numpy=True)
        
        # Load all vectors from DB if not in memory
        if not self.vectors:
            self._load_all_vectors()
        
        # Compute similarities
        similarities = []
        for doc_id, vector in self.vectors.items():
            # Cosine similarity
            sim = np.dot(query_embedding, vector) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(vector) + 1e-8
            )
            similarities.append((self.texts[doc_id], float(sim)))
        
        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:k]
    
    def _load_all_vectors(self):
        """Load all vectors from database into memory."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, text, vector FROM vectors")
        for doc_id, text, vector_bytes in cursor.fetchall():
            self.vectors[doc_id] = pickle.loads(vector_bytes)
            self.texts[doc_id] = text
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()


# Global instance
_store: Optional[SimpleVectorStore] = None

def get_vector_store() -> SimpleVectorStore:
    """Get or create global vector store instance."""
    global _store
    if _store is None:
        _store = SimpleVectorStore()
    return _store

def close_vector_store():
    """Close global vector store."""
    global _store
    if _store:
        _store.close()
        _store = None
