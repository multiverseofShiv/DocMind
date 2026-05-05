from functools import lru_cache
from sentence_transformers import CrossEncoder
from langchain_core.documents import Document

from app.core.config import get_settings


@lru_cache(maxsize=1)
def get_cross_encoder() -> CrossEncoder:
    settings  = get_settings()
    
    return CrossEncoder(settings.reranker_model)

def rerank(query:str, docs:list[Document], top_k: int |None= None)-> list[Document]:
    if not docs:
        return[]
    settings = get_settings()
    top_k = top_k or settings.reranker_top_k
    
    encoder = get_cross_encoder()
    pairs = [(query, d.page_content) for d in docs]
    scores = encoder.predict(pairs)
    
    scored = sorted(zip(scores,docs), key= lambda x:x[0], reverse= True)
    return [doc for _, doc in scored[:top_k]]