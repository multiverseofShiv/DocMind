import logging
from langchain_groq import ChatGroq
from langchain_community.chat_models import ChatOllama

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def get_llm():
    
    s = get_settings()
    
    if s.llm_provider.lower()=="groq" and s.groq_api_key:
        return ChatGroq(
            model= s.llm_model,
            temperature= s.llm_temperature,
            api_key= s.groq_api_key,
        )
        
    logger.warning("Falling Back to ollama (%s)", s.ollama_model)
    return ChatOllama (
        model= s.ollama_model_model, 
        base_url= s.ollama_base_url,
        temperature= s.llm_temperature)