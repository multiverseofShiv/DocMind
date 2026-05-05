from functools import lru_cache
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever

from app.services.ingestion import get_qdrant_client, get_vector_store
from app.core.config import get_settings

def _load_all_chunks(tenant_id : str | None=None) -> list[Document]:
    settings = get_settings()
    client = get_qdrant_client()
    collection = settings.qdrant_collection if not tenant_id else f"m{tenant_id}"
    docs: list[Document] = []
    next_offset = None
    while True:
        points, next_offset = client.scroll(
            collection_name= collection,
            limit = 512,
            offset= next_offset,
            with_payload= True,
            with_vectors= False,
        )
        for p in points:
            payload = p.payload or {}
            content = payload.get("page_content") or payload.get("content") or ""
            metadata = payload.get("metadata") or {}
            docs.append(Document(page_content=content, metadata = metadata))
        if next_offset is None:
            break
    return docs


@lru_cache(maxsize=1)
def get_hybrid_retriever(tenant_id: str | None=None) -> BaseRetriever:
    
    s = get_settings()

    dense = get_vector_store(tenant_id=tenant_id).as_retriever(serch_kwargs={"k": s.top_k_initial})
    

    chunks = _load_all_chunks(tenant_id=tenant_id)
    
    if chunks:
        bm25 = BM25Retriever.from_documents(chunks)
        bm25.k = s.top_k_initial
        
        return EnsembleRetriever(retrievers=[dense, bm25], weights=[0.5,0.5])

    return dense


    
    