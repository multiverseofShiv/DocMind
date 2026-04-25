from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from app.core.config import get_settings
from app.services.embeddings import get_embeddings


def _ensure_collection(client: QdrantClient, name: str, dim: int)-> None:
    
    existing = {c.name for c in client.get_collections().collections}
    if name not in existing:
        client.create_collection(
            collection_name= name,
            vectors_config = VectorParams(size = dim, distance= Distance.COSINE)
        )
        

def laod_pdf(path: str | Path) -> list:
    pages = PyPDFLoader(str(path)).load()
    return pages[6:10]

def chunk_documents(docs:list, chunk_size:int, overlap: int)->list:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size = chunk_size,
        chunk_overlap = overlap,
        separators=["\n\n","\n",". "," ",""]
    )
    return splitter.split_documents(docs)


def ingest(pdf_path: str | Path, collection: str | None = None) -> int:
    
    settings = get_settings()
    collection = collection or settings.qdrant_collection
    
    client = QdrantClient(url= settings.qdrant_url, api_key= settings.qdrant_api_key)
    _ensure_collection(client, collection, settings.embedding_dim)
    
    
    docs = laod_pdf(pdf_path)
    
    chunks = chunk_documents(docs, settings.chunk_size, settings.chunk_overlap)
    
    for c in chunks:
        c.metadata["source"] = Path(pdf_path).name
        
    vector_store = QdrantVectorStore(
        client=client,
        collection_name= collection,
        embedding= get_embeddings()
    )
    
    vector_store.add_documents(chunks)
    return len(chunks)


    
    
    









