from fastapi import FastAPI

from app.api.routes import chat

app = FastAPI(title="DocMind", version="0.1.0")

app.include_router(chat.router)

@app.get("/health")
def health():
    return {"status":"ok"}
