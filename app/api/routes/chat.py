from fastapi import APIRouter, HTTPException

from app.models.schemas import ChatRequest, ChatResponse
from app.services.rag import build_rag_chain

router = APIRouter(tags=["chat"])

@router.post("/chat", response_model= ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    try:
        chain =  build_rag_chain(k=req.top_k)
        answer = chain.invoke(req.question)
        return ChatResponse(answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail= str(e))