import time

from fastapi import APIRouter, Depends, HTTPException, Request
from langchain_core.prompts import ChatPromptTemplate
from slowapi import Limiter

from app.services.metrics import log_request
from app.core.config import get_settings
from app.utils.token_counter import count_tokens, estimate_cost
from app.services.cache import semantic_cache
from app.gaurdrail.injection_detector import detect_injection
from app.gaurdrail.pii_redactor import redact
from app.core.security import verify_api_key
from app.services.llm import get_llm
from app.models.schemas import ChatRequest, RAGAnswer
from app.services.rag import _format_docs, retrieve_and_rerank
from app.core.rate_limit import limiter
from app.services.tracing import trace_chat

router = APIRouter(tags=["chat"])

_PROMPT = ChatPromptTemplate.from_template(
    "Answer ONLY from this context:\n{context}\n\n"
    "If the context doesn't answer, say \"I don't know\"\n\n"
    "Question: {question}\nAnswer:"
)


def _run_chain(context: str, redacted_query: str, tenant_id: str) -> RAGAnswer:
    chain = _PROMPT | get_llm().with_structured_output(RAGAnswer)
    return chain.invoke(
        {"context": context, "question": redacted_query},
        config={
            "metadata": {"user_id": tenant_id},
            "tags": ["chat", "production"]
        }
    )


@router.post("/chat", response_model=RAGAnswer)
@limiter.limit(get_settings().rate_limit_chat)
def chat(request: Request, req: ChatRequest, tenant_id: str = Depends(verify_api_key)) -> RAGAnswer:
    settings = get_settings()
    t0 = time.perf_counter()

    is_inj, inj_score, inj_matches = detect_injection(req.query)

    if is_inj:
        raise HTTPException(status_code=400, detail=f"prompt injection detected (Score={inj_score})")

    redacted_query, redaction_summary = redact(req.query)

    cached = semantic_cache.get(redacted_query, tenant_id)

    if cached is not None:
        latency = int((time.perf_counter() - t0) * 1000)
        log_request(
            tenant_id=tenant_id, query=req.query, model=settings.llm_model,
            tokens_in=0, tokens_out=0, cost_usd=0.0,
            latency_ms=latency, cache_hit=True
        )
        return RAGAnswer(**cached) if isinstance(cached, dict) else cached

    print(f"tenant_id is :{tenant_id}\n\n")

    docs = retrieve_and_rerank(
        redacted_query,
        tenant_id=tenant_id,
        use_hyde=req.use_hyde,
        use_multi_query=req.use_multi_query
    )

    context = _format_docs(docs)
    answer = _run_chain(context, redacted_query, tenant_id)

    semantic_cache.set(
        query=redacted_query,
        tenant_id=tenant_id,
        answer=answer.model_dump() if hasattr(answer, "dict") else answer
    )

    prompt_text = f"{context}\n{redacted_query}"
    tokens_in = count_tokens(prompt_text, model=settings.llm_model)
    out_text = answer.answer
    tokens_out = count_tokens(out_text, model=settings.llm_model)
    cost = estimate_cost(tokens_in, tokens_out, settings.llm_model)
    latency = int((time.perf_counter() - t0) * 1000)

    log_request(
        tenant_id=tenant_id, query=req.query, model=settings.llm_model, tokens_in=tokens_in,
        tokens_out=tokens_out, cost_usd=cost, latency_ms=latency, cache_hit=False,
    )

    trace_chat(
        tenant_id=tenant_id,
        query=redacted_query,
        answer=answer.answer,
        latency_ms=latency,
    )
    print(f"\n logged successfully \n")

    return answer