from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
# from langchain_qdrant import QdrantVectorStore
# from qdrant_client import QdrantClient

from app.models.schemas import RAGAnswer
from app.services.query_transform import hyde, multi_query
from app.services.reranker import rerank
from app.services.retrieval import get_hybrid_retriever
# from app.core.config import get_settings
# from app.services.embeddings import get_embeddings
from app.services.llm import get_llm
from langchain_core.documents import Document

# SYSTEM_PROMPT = """You are a helpful assistant . Answer the user's question using only the provided context. If the answer is not in the context , say "I don't know based on the provided documents." Be concise and cite page numbers when helpful.
# Provide the answer in below format:
# 1. Direct answer (1 line)
# 2. Mechanism (how it works)
# 3. Outcome (impact)
# 4. Citation

# context : {context}
# """
SYSTEM_PROMPT = """You are a precise RAG assistant. Answer ONLY using the provided context.

Instructions:
1. Provide a clear, concise answer grounded exclusively in the context.
2. For each factual claim, cite the source with [source p.N] where source is the document name and N is the page number.
3. Extract citations: For each document chunk used, provide:
   - document_name: The source filename from the context
   - page: The page number from [source p.N]
   - snippet: A short verbatim quote (≤200 chars) from that chunk supporting your answer
4. Rate confidence 0-1:
   - 1.0: Context fully answers the question with high relevance
   - 0.7-0.9: Context answers but with some gaps or partial relevance
   - 0.4-0.6: Context provides some information but doesn't fully answer
   - 0.0-0.3: Context barely addresses the question or requires significant inference

If the context is insufficient to answer, say so and lower confidence accordingly."""


def _dedupe(docs: list[Document]) -> list[Document]:
    seen: set[tuple] = set()
    out: list[Document] = []
    for d in docs:
        key = (d.metadata.get("source"), d.metadata.get("page"), d.page_content[:50])
        if key not in seen:
            seen.add(key)
            out.append(d)
    return out
    



prompt = ChatPromptTemplate.from_messages(
    [("system", SYSTEM_PROMPT),
     ('human', "Question: {question}\n\nContext:\n{context}")]
)


def _format_docs(docs)-> str:
    parts = []
    for d in docs:
        src = d.metadata.get("source", "unknown")
        page = d.metadata.get("page")
        tag = f"[{src} p.{page}]" if page is not None else f"[{src}]"
        parts.append(f"{tag}\n{d.page_content}")
    return "\n\n".join(parts)

# ensemble = get_hybrid_retriever()


def retrieve_and_rerank(
                        question: str,
                        *,
                        tenant_id: str | None = None,
                        use_hyde: bool = False,
                        use_multi_query: bool = False,)-> list[Document]:
    
    retriever = get_hybrid_retriever(tenant_id = tenant_id)
    
    if use_multi_query:
        queries = multi_query(question, n=3)
    elif use_hyde:
        queries = [hyde(question)]
    else:
        queries = [question]
    
    
    candidates : list[Document] = []
    for q in queries:
        candidates.extend(retriever.invoke(q))
        
        # for doc in retriever.invoke(q):
        #     key = doc.page_content
        #     if key not in seen:
        #         seen.add(key)
        #         candidates.append(doc)
    candidates = _dedupe(candidates)       
                
    reranked = rerank(question, candidates)
    
    
    print(f"[retrieve] hyde={use_hyde} mq={use_multi_query}"
          f"queries={len(queries)} candidates={len(candidates)} -> top={len(reranked)}")
    
    return reranked
        
        
                        

# def retrieve_and_rerank(question: str):
#     candidates = ensemble.invoke(question)
#     reranked = rerank(question, candidates)
#     print(f"[rerank]{len(candidates)}-> top{len(reranked)}")
#     for i, d in enumerate(reranked):
#         print(f" #{i+1} p{d.metadata.get('page')} :: {d.page_content[:80]}")
#     return reranked


# def get_retriever(k: int =5):
#     s= get_settings()
#     client = QdrantClient(url= s.qdrant_url)
#     vs = QdrantVectorStore(
#         client=client,
#         collection_name= s.qdrant_collection,
#         embedding= get_embeddings()
#     )
#     return vs.as_retriever(search_kwargs={"k":k})


def build_rag_chain(k: int=5):
    retriever = get_hybrid_retriever()
    # llm = get_llm()
    return (
        # {
        #     "context": retriever | _format_docs, "question": RunnablePassthrough()}
        # {
        #     "context": RunnableLambda(retrieve_and_rerank)| _format_docs,"question": RunnablePassthrough()
        # }
        {
            "context": (lambda x: x["question"]) |RunnableLambda(retrieve_and_rerank)| RunnableLambda(_format_docs), "question": lambda x:x["question"]
        }
        | prompt
        | get_llm().with_structured_output(RAGAnswer)
        | StrOutputParser()
    )