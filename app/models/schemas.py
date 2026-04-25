from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    question: str = Field (..., min_length=1)
    top_k: int = Field(5, ge=1, le=15)
    

class ChatResponse(BaseModel):
    answer: str