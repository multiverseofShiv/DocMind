from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    query: str
    use_hyde: bool= False
    use_multi_query: bool = False
    # question: str = Field (..., min_length=1)
    # top_k: int = Field(5, ge=1, le=15)
    
class Citation(BaseModel):
    document_name : str = Field(..., description="Source filename, e.g. 'paper.pdf' ")
    page: int = Field(..., description="1-based page no from metadata")
    snippet: str = Field(..., description="Short quote (<=200 chars) from chunk supporting the claim")
    
    
class RAGAnswer(BaseModel):
    answer: str = Field(..., description="Final Answer grounded ONLY in provided context")
    citations: list[Citation] = Field(default_factory= list, description= "One per source chunk actually used")
    confidence: float = Field(...,ge=0.0,le=1.0, description="Self rated 0-1 based on the context coverage")
    

class ChatResponse(BaseModel):
    answer: str