import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.config import PROCESSED_DATA_PATH


class ResolutionRetriever:
    """
    Retriever for historical customer support resolutions.
    Uses TF-IDF + Cosine similarity (fast, deterministic, zero external API latency)
    with optional ChromaDB integration for dense embeddings.
    """

    def __init__(self, data_path: Path = PROCESSED_DATA_PATH):
        self.data_path = data_path
        self.documents: List[Dict[str, Any]] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        self._is_indexed = False

    def build_index(self, max_records: int = 4000):
        """Build the in-memory search index from processed paired dataset."""
        if not self.data_path.exists():
            print(f"[!] Warning: Data path {self.data_path} not found. Retriever index empty.")
            return

        print(f"[*] Building retriever index from: {self.data_path}")
        self.documents = []
        with open(self.data_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    self.documents.append(json.loads(line))
                if len(self.documents) >= max_records:
                    break

        corpus = [doc["customer_text"] for doc in self.documents]
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=10000,
            ngram_range=(1, 2)
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
        self._is_indexed = True
        print(f"[✓] Indexed {len(self.documents)} historical resolution pairs.")

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Retrieve top_k most similar historical customer inquiries and their resolutions."""
        if not self._is_indexed or self.vectorizer is None or self.tfidf_matrix is None:
            self.build_index()

        if not self.documents:
            return []

        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        
        # Get top indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            doc = self.documents[idx]
            results.append({
                "id": doc.get("id", idx + 1),
                "customer_text": doc["customer_text"],
                "brand_reply_text": doc["brand_reply_text"],
                "similarity_score": round(score, 4)
            })

        return results


# Global singleton instance for easy import across modules
_retriever_instance = None

def get_retriever() -> ResolutionRetriever:
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = ResolutionRetriever()
        _retriever_instance.build_index()
    return _retriever_instance
