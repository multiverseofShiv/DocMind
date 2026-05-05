from langchain_community.retrievers import BM25Retriever
from langchain_qdrant import QdrantVectorStore
from app.services.retrieval import get_hybrid_retriever


retriever = get_hybrid_retriever()
query= "What are the major components of a financial plan?"

dense, bm25 = retriever.retrievers

print("-- Dense top 5 ---")
for d in dense.invoke(query)[:5]:
    print(d.metadata.get("source"), d.metadata.get("page"),"|", d.page_content[:80])
    
print("\n-- BM25 top 5 --")
for d in bm25.invoke(query)[:5]:
    print(d.metadata.get("source"), d.metadata.get("page"),"|", d.page_content[:80])
    
print("\n-- Ensemble top 5 --")
for d in retriever.invoke(query)[:5]:
    print(d.metadata.get("source"), d.metadata.get("page"),"|", d.page_content[:80])
    