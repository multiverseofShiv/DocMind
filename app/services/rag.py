from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from app.core.config import get_settings
from app.services.embeddings import get_embeddings
from app.services.llm import get_llm

SYSTEM_PROMPT = """You are a helpful assistant . Answer the user's question using only the provided context. If the answer is not in the context , say "I don't know based on the provided documents." Be concise and cite page numbers when helpful.

context : {context}
"""

prompt = ChatPromptTemplate.from_messages(
    [("system", SYSTEM_PROMPT),('human', "{question}")]
)


def _format_docs(docs)-> str:
    parts = []
    for d in docs:
        src = d.metadata.get("source", "unknown")
        page = d.metadata.get("page")
        tag = f"[{src} p.{page}]" if page is not None else f"[{src}]"
        parts.append(f"{tag}\n{d.page_content}")
    return "\n\n".join(parts)


def get_retriever(k: int =5):
    s= get_settings()
    client = QdrantClient(url= s.qdrant_url)
    vs = QdrantVectorStore(
        client=client,
        collection_name= s.qdrant_collection,
        embedding= get_embeddings()
    )
    return vs.as_retriever(search_kwargs={"k":k})


def build_rag_chain(k: int=5):
    retriever = get_retriever(k=k)
    llm = get_llm()
    return (
        {
            "context": retriever | _format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )