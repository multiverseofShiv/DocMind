from functools import lru_cache
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from app.core.config import get_settings

@lru_cache
def get_embeddings()->HuggingFaceEmbeddings:
    
    settings = get_settings()
    
    return HuggingFaceEmbeddings(model_name= settings.embedding_model,
                                 model_kwargs={"device": "cpu"},
                                 encode_kwargs={"normalize_embeddings":True},
                                 )
