import re
from typing import List, Dict, Tuple, Any
import math

class SemanticEngine:
    """[CPOS v2.0] Lightweight Semantic Search Engine. 
    Uses TF-IDF style keyword weighting to simulate vector search without external heavy dependencies."""
    
    def __init__(self):
        self.stop_words = {"the", "is", "at", "which", "on", "and", "a", "an", "to", "in", "of", "for"}

    def _tokenize(self, text: str) -> List[str]:
        # Lowercase and split by non-alphanumeric
        words = re.findall(r'\w+', text.lower())
        return [w for w in words if w not in self.stop_words]

    def _calculate_score(self, query_tokens: List[str], doc_tokens: List[str]) -> float:
        if not query_tokens or not doc_tokens: return 0.0
        
        matches = 0
        for q in query_tokens:
            if q in doc_tokens:
                matches += 1
        
        # Simple overlap coefficient
        return matches / len(query_tokens)

    def search(self, query: str, objects: List[Any], limit: int = 3) -> List[Tuple[Any, float]]:
        query_tokens = self._tokenize(query)
        results = []
        
        for obj in objects:
            # Combine title and summary for "semantic" context
            content = f"{obj.title} {obj.summary} {obj.type}"
            doc_tokens = self._tokenize(content)
            score = self._calculate_score(query_tokens, doc_tokens)
            
            if score > 0:
                results.append((obj, score))
        
        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]
