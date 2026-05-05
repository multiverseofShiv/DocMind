import json
import time

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.services.tracing import get_callbacks
from app.utils.token_counter import count_tokens, estimate_cost
from app.core.config import get_settings
from app.core.security import verify_api_key
from app.models.schemas import ChatRequest
from app.services.llm import get_llm
from app.services.rag import _format_docs, retrieve_and_rerank
from app.services.metrics import log_request
from app.core.rate_limit import limiter

router = APIRouter()

_Stream_prompt = ChatPromptTemplate.from_template(
    "Answer only from the context below. cite sources inline using the"
    "[source p.N] tags exactly as they appear. if the context does'nt matter"
    "say so.\n\n"
    "Context:\n{context}\n\n"
    "Question:{question}\nAnswer"
)


def _sse(event:str, data)->str:
    
    payload= data if isinstance(data, str) else json.dumps(data)
    return f"event: {event}\n data:{payload}\n\n"

@router.post("/chat/stream")
@limiter.limit(get_settings().rate_limit_chat)
def chat_stream(request: Request, req: ChatRequest, tenant_id: str = Depends(verify_api_key)) -> StreamingResponse:
    
    settings = get_settings()
    
    def generate():
        
        t0 = time.perf_counter()
        
        docs= retrieve_and_rerank(
            req.query,
            tenant_id = tenant_id,
            use_hyde=req.use_hyde,
            use_multi_query=req.use_multi_query,
        )
        sources = [
            {"document_name": d.metadata.get("source","unknown"),
            "page": d.metadata.get("page"),
            }for d in docs
        ]
        yield _sse("sources",sources)
        
        #streaming response 
        
        answer_parts : list[str] = []
        context = _format_docs(docs)
        chain = _Stream_prompt | get_llm()| StrOutputParser()
        callbacks = get_callbacks(tenant_id = tenant_id, tags=["chat-stream"])
        config = {"callbacks":callbacks} if callbacks else {}
        
        for chunk in chain.stream({"context": context, "question": req.query}, config=config):
            if chunk:
                answer_parts.append(chunk)
                yield _sse("token",{"text":chunk})
                
        yield _sse("done", {"ok":True})
        
        #token+cost
        full_answer ="".join(answer_parts)
        tokens_in = count_tokens(f"{context}\n{req.query}", model = settings.llm_model)
        tokens_out = count_tokens(full_answer, model = settings.llm_model)
        cost = estimate_cost(tokens_in, tokens_out, settings.llm_model)
        latency = int((time.perf_counter() - t0) * 1000)
        log_request(
            tenant_id = tenant_id, query = req.query, model = settings.llm_model, tokens_in = tokens_in,
            tokens_out = tokens_out, cost_usd = cost, latency_ms = latency, cache_hit = False, 
        )
            
    return StreamingResponse(generate(), media_type="text/event-stream")