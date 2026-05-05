from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.services.llm import get_llm

_HYDE_PROMPT = ChatPromptTemplate.from_template(
    "Write a short factual paragraph (2-4 sentences) that would directly "
    "answer the following question. Do not add disclaimer.\n\n"
    "Question: {question}\n\nPassage:"
)

_MULTI_QUERY_PROMPT = ChatPromptTemplate.from_template(
    "Generate {n} alternative phrasing of the user question below. "
    "Each phrasing should preserve meaning but vary vocabulary and structure. "
    "Return ONLY the {n} questions, one per line, no numbering or extra text.\n\n"
    "Original question: {question}"
)

def hyde(question: str)-> str:
    chain = _HYDE_PROMPT | get_llm() | StrOutputParser()
    return chain.invoke({"question": question}).strip()

def multi_query(question: str, n: int=3)-> list[str]:
    chain = _MULTI_QUERY_PROMPT | get_llm() | StrOutputParser()
    
    raw = chain.invoke({"question": question, "n":n})
    variants = [line.strip() for line in raw.splitlines() if line.strip()]
    return [question] + variants[:n]
    
    
    