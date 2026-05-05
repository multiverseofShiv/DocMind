from typing import Optional
import hashlib
from fastapi import Header, HTTPException,status
from pydantic import BaseModel
from app.core.config import get_settings
import psycopg

class APIKeyRecord(BaseModel):
    tenant_id: str
    active: bool
    
def _hash_key(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()

def get_db_conn():
    settings = get_settings()
    return psycopg.connect(settings.postgres_url)


def verify_api_key(x_api_key: Optional[str] = Header(None))-> str:
    
    if not x_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key")
    
    key_hash = _hash_key(x_api_key)
    
    try:
        with get_db_conn().cursor() as cur:
            cur.execute("SELECT tenant_id, active FROM api_key WHERE key_hash = %s", (key_hash,))
            row = cur.fetchone()
            
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Auth DB Error")
    
    if not row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    
    tenant_id, active = row
    if not active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="API key inactive")
    
    
    return tenant_id