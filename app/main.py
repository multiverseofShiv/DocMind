from fastapi import FastAPI
from slowapi.errors import RateLimitExceeded


from app.api.routes import chat,chat_stream,metrics
from app.core.rate_limit import limiter, rate_limit_handler

app = FastAPI(title="DocMind", version="0.1.0")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)


app.include_router(chat.router, tags=["chat"])
app.include_router(chat_stream.router, tags=["chat"])
app.include_router(metrics.router, tags=["metrics"])

@app.get("/health")
def health():
    return {"status":"ok"}
