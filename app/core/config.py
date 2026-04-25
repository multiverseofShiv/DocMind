from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file= ".env",
        env_file_encoding="utf-8",
        case_sensitive= False,
        extra= "ignore"
    )


    app_name : str = "DocMind"
    environment : str = "Dev"
    log_level: str = "INFO"


    llm_provider: str = "groq"
    llm_model: str = "llama-3.3-70b-versatile"
    llm_temperature: float = 0.0
    groq_api_key: str | None = None
    ollama_base_url: str = " https://lugged-guide-although.ngrok-free.dev/"
    ollama_model : str = "gemma3:1b"


    #embeddings/reranker
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dim: int = 384
    reranker_model : str = "BAAI/bge-reranker-base"

    #qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    qdrant_collection: str = "documents"

    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 3600
    cache_similarity_threshold: float = 0.95



    postgres_url: str = "postgresql+psycopg://docmind:docmind@localhost:5432/docmind"

    # retrieval

    top_k_initial: int =20
    top_k_final: int =5
    chunk_size: int=500
    chunk_overlap: int=50


@lru_cache
def get_settings() -> Settings:
    """Cached Singelton"""
    return Settings()