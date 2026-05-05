import os 
import secrets
import hashlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


from app.core.config import get_settings
import psycopg
from app.services.ingestion import ingest


def _hash_key(k:str) -> str:
    return hashlib.sha256(k.encode("utf-8")).hexdigest()

def main():
    s = get_settings()
    print("Settings URL:", s.postgres_url)
    
    sample_dir = ROOT/"data"/"sample"
    
    pdfs = sorted(sample_dir.glob("*.pdf"))
    
    with psycopg.connect(s.postgres_url) as conn:
        with conn.cursor() as cur:
            for tenant in ("tenant_a", "tenant_b"):
                api_key = secrets.token_urlsafe(24)
                key_hash = _hash_key(api_key)
                cur.execute(
                            "INSERT INTO api_key (key_hash, tenant_id, active) VALUES (%s,%s, true) ON CONFLICT (key_hash) DO NOTHING",
                            (key_hash, tenant),
)
                
                print(f"Created tenant {tenant} with API key: {api_key}")
                
                
    if pdfs:
        print("Ingesting sample PDFs into tenant_a and tenant_b collections")
        ingest([str(p) for p in pdfs], tenant_id="tenant_a")
        ingest([str(p) for p in pdfs], tenant_id="tenant_b")
        print("Ingestion_complete")
        
    else:
        print("No sample pdf's found; skipped ingestion")
        
        
if __name__ == "__main__":
    main()
                
    