import pickle
import hashlib
import numpy as np
from typing import Optional, Dict, List

from app.core.config import get_settings

try:
    import redis
except ImportError:
    redis = None

from .embeddings import get_embeddings

settings = get_settings()


def normalize(vec: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vec)
    return vec if norm == 0 else vec / norm


class SemanticCache:
    def __init__(
        self,
        redis_url: Optional[str] = None,
        threshold: float = 0.85,
        ttl: int = 3600,
        max_memory_entries: int = 100,
    ):
        self.threshold = threshold
        self.ttl = ttl
        self.max_memory_entries = max_memory_entries

        self.embedding_model = get_embeddings()
        self.redis_url = redis_url or settings.redis_url

        self.enabled = False
        self.r = None
        self._memory_cache: Dict[str, List[Dict]] = {}

        self.__init_backend()

    # -----------------------------
    # INIT REDIS
    # -----------------------------
    def __init_backend(self):
        if redis is not None:
            try:
                self.r = redis.Redis.from_url(self.redis_url)
                self.r.ping()
                self.enabled = True
                print(f"[CACHE INIT] Redis connected: {self.redis_url}")
            except Exception as e:
                print(f"[CACHE INIT ERROR] {e}")
                self.r = None
                self.enabled = False
        else:
            self.enabled = False

    # -----------------------------
    # KEY
    # -----------------------------
    def _make_key(self, tenant_id: str, query: str) -> str:
        q_hash = hashlib.sha256(query.encode()).hexdigest()
        return f"cache:{tenant_id}:{q_hash}"

    # -----------------------------
    # EMBEDDING
    # -----------------------------
    def _get_embedding(self, query: str) -> np.ndarray:
        emb = self.embedding_model.embed_query(query)
        return normalize(np.array(emb, dtype=np.float32))

    # -----------------------------
    # GET
    # -----------------------------
    def get(self, query: str, tenant_id: str):
        print(f"[CACHE GET] tenant={tenant_id}")

        query_embedding = self._get_embedding(query)

        if self.enabled and self.r:
            try:
                pattern = f"cache:{tenant_id}:*"
                for key in self.r.scan_iter(match=pattern):
                    data = self.r.get(key)
                    if not data:
                        continue

                    entry = pickle.loads(data)
                    cached_embedding = normalize(
                        np.array(entry["embedding"], dtype=np.float32)
                    )

                    sim = float(np.dot(query_embedding, cached_embedding))

                    if sim >= self.threshold:
                        print(f"[CACHE HIT] key={key}")
                        return entry["answer"]

            except Exception as e:
                print(f"[CACHE GET ERROR] {e}")

            print("[CACHE MISS]")
            return None

        # fallback
        entries = self._memory_cache.get(tenant_id, [])
        for entry in entries:
            cached_embedding = normalize(
                np.array(entry["embedding"], dtype=np.float32)
            )
            sim = float(np.dot(query_embedding, cached_embedding))
            if sim >= self.threshold:
                print("[CACHE HIT - MEMORY]")
                return entry["answer"]

        print("[CACHE MISS]")
        return None

    # -----------------------------
    # SET
    # -----------------------------
    def set(self, query: str, tenant_id: str, answer, ttl: Optional[int] = None):
        print(f"[CACHE SET] tenant={tenant_id}")

        embedding = self._get_embedding(query)
        entry = {
            "query": query,
            "embedding": embedding.tolist(),
            "answer": answer,
        }

        ttl = ttl or self.ttl

        if self.enabled and self.r:
            key = self._make_key(tenant_id, query)
            try:
                self.r.setex(key, ttl, pickle.dumps(entry))
                print(f"[REDIS WRITE] key={key}")
                return
            except Exception as e:
                print(f"[CACHE SET ERROR] {e}")

        # fallback
        if tenant_id not in self._memory_cache:
            self._memory_cache[tenant_id] = []

        self._memory_cache[tenant_id].append(entry)

        if len(self._memory_cache[tenant_id]) > self.max_memory_entries:
            self._memory_cache[tenant_id].pop(0)

    # -----------------------------
    # INVALIDATE
    # -----------------------------
    def invalidate_tenant(self, tenant_id: str):
        if self.enabled and self.r:
            pattern = f"cache:{tenant_id}:*"
            for key in self.r.scan_iter(match=pattern):
                self.r.delete(key)

        if tenant_id in self._memory_cache:
            del self._memory_cache[tenant_id]


# singleton
semantic_cache = SemanticCache()