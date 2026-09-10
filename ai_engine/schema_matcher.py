import math
import difflib
from typing import List, Dict, Optional

try:
    from sentence_transformers import SentenceTransformer, util
    _st_model = None
    def get_st_model():
        global _st_model
        if _st_model is None:
            # Use small, fast 22MB sentence-transformer model
            _st_model = SentenceTransformer("all-MiniLM-L6-v2")
        return _st_model
    ST_AVAILABLE = True
except Exception:
    ST_AVAILABLE = False

class SchemaMatcher:
    def __init__(self, use_embeddings: bool = True):
        self.use_embeddings = use_embeddings and ST_AVAILABLE

    def normalize_field_name(self, text: str) -> str:
        # Convert camelCase, snake_case, etc to space-separated words
        res = []
        for char in text:
            if char.isupper():
                res.append(" " + char.lower())
            elif char in ("_", "-"):
                res.append(" ")
            else:
                res.append(char)
        return "".join(res).strip()

    def compute_similarity(self, field1: str, field2: str) -> float:
        norm1 = self.normalize_field_name(field1)
        norm2 = self.normalize_field_name(field2)

        if self.use_embeddings:
            try:
                model = get_st_model()
                emb1 = model.encode(norm1, convert_to_tensor=True)
                emb2 = model.encode(norm2, convert_to_tensor=True)
                sim = float(util.cos_sim(emb1, emb2)[0][0])
                return round(sim, 4)
            except Exception:
                pass

        # String similarity fallback (SequenceMatcher + word token match)
        ratio = difflib.SequenceMatcher(None, norm1, norm2).ratio()
        # boost if token words match exactly (e.g. customer id vs customerid)
        if norm1.replace(" ", "") == norm2.replace(" ", ""):
            ratio = 1.0
        return round(ratio, 4)

    def find_best_match(self, unexpected_field: str, expected_fields: List[str], threshold: float = 0.70) -> Optional[Dict[str, any]]:
        best_field = None
        best_score = 0.0

        for exp in expected_fields:
            score = self.compute_similarity(unexpected_field, exp)
            if score > best_score:
                best_score = score
                best_field = exp

        if best_score >= threshold and best_field:
            return {
                "unexpected_field": unexpected_field,
                "mapped_to_field": best_field,
                "confidence": best_score
            }
        return None
