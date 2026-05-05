from pathlib import Path
from typing import Iterable
from langchain_community.document_loaders import PyPDFLoader
# from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from langchain_classic.retrievers import ParentDocumentRetriever
from langchain_core.documents import Document

from app.core.config import get_settings
from app.services.embeddings import get_embeddings






        

def load_pdf(path: str | Path) -> list[Document]:
    docs = PyPDFLoader(str(path)).load()
    name = Path(path).name
    for d in docs:
        d.metadata["source"] = name
        if "page" in d.metadata:
            d.metadata["page"] = int(d.metadata["page"])+1
    return docs
    
    # pages = PyPDFLoader(str(path)).load()
    # return pages[6:10]

def chunk_documents(docs:Iterable[Document])-> list[Document]:
    settings = get_settings()
    docs  = list(docs)
    strategy = getattr(settings,"chunking_strategy","recursive").lower()
    if strategy == "recursive":
        splitter = RecursiveCharacterTextSplitter(
            chunk_size = settings.chunk_size,
            chunk_overlap = settings.chunk_overlap,
            separators=["\n\n","\n",". "," ",""]
        )
        return splitter.split_documents(docs)
    # elif strategy =="semantic":
    #     embedder = HuggingFaceEmbeddings(model_name = settings.embedding_model )
    #     splitter = SemanticChunker(
    #         embedder,
    #         chunk_size = settings.chunk_size,
    #         chunk_overlap = settings.overlap,
    #     )
    elif strategy == "parentdoc":
        splitter = RecursiveCharacterTextSplitter(
            chunk_size = settings.chunk_size * 3,
            chunk_overlap = settings.overlap,
            separators=["\n\n","\n",". "," ",""]
        )
        parent_retriever = ParentDocumentRetriever(
            child_splitter = splitter,
            chunk_size = settings.chunk_size * 3,
            chunk_overlap = settings.overlap,
            separators=["\n\n","\n",". "," ",""] 
        )
        parent_docs = parent_retriever.transform_documents(docs)
        return [child for parent in parent_docs for child in parent.metadata["children"]]
    else:
        raise ValueError(f"Unknown Chunking Strategy: {strategy}")

def _ensure_collection(client: QdrantClient, name: str, dim: int)-> None:
    settings = get_settings()
    existing = {c.name for c in client.get_collections().collections}
    if name not in existing:
        client.create_collection(
            collection_name= name,
            vectors_config = VectorParams(size = dim, distance= Distance.COSINE)
        )
        
def get_qdrant_client() -> QdrantClient:
    settings = get_settings()
    return QdrantClient(settings.qdrant_url)

def get_vector_store(tenant_id: str| None = None)-> QdrantVectorStore:
    settings = get_settings()
    client = get_qdrant_client()
    collection_name = settings.qdrant_collection if not tenant_id else f"m{tenant_id}"
    _ensure_collection(client, collection_name, settings.embedding_dim)
    return QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=get_embeddings()
    )
    
    



def ingest(paths: list[str | Path], tenant_id: str | None = None) -> int:
    
    all_docs : list[Document] = []
    
    for p in paths:
        all_docs.extend(load_pdf(p))
    chunks = chunk_documents(all_docs)
    store = get_vector_store(tenant_id=tenant_id)
    store.add_documents(chunks)
    
    # collection = collection or settings.qdrant_collection
    
    # client = QdrantClient(url= settings.qdrant_url, api_key= settings.qdrant_api_key)
    # _ensure_collection(client, collection, settings.embedding_dim)
    
    
    
    # docs = laod_pdf(pdf_path)
    
    # chunks = chunk_documents(docs, settings.chunk_size, settings.chunk_overlap)
    
    # for c in chunks:
    #     c.metadata["source"] = Path(pdf_path).name
        
    # vector_store = QdrantVectorStore(
    #     client=client,
    #     collection_name= collection,
    #     embedding= get_embeddings()
    # )
    
    # vector_store.add_documents(chunks)
    return len(chunks)


    
    
    









