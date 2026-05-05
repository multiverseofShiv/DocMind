from __future__ import annotations

import logging
from typing import Any

import psycopg

from app.core.config import get_settings

logger = logging.getLogger(__name__)

def log_request(
    *,
    tenant_id: str,
    query: str,
    model: str|None,
    tokens_in: int,
    tokens_out: int,
    cost_usd: float,
    latency_ms: int,
    cache_hit: bool
)-> None:
    
    settings = get_settings()
    
    try:
        with psycopg.connect(settings.postgres_url) as conn:
            with conn.cursor() as cur:
                print("\nConnected to Postgres - metrics\n")
                
                cur.execute(
                    """
                    INSERT INTO requests(
                        tenant_id, query, model, tokens_in, tokens_out, cost_usd, latency_ms, cache_hit
                    )
                    VALUES(%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        tenant_id, query, model, tokens_in, tokens_out, cost_usd, latency_ms, cache_hit
                    )
                )
                # Commit is handled automatically by the 'with conn' block in psycopg3
                print("\nQuery executed\n")
                
    except Exception as e:
        print(f"Failed to log metrics: {e}")
        
def tenant_aggregates(tenant_id: str) -> dict[str, Any]:
    
    settings = get_settings()
    
    sql = """
        SELECT
            COUNT(*) AS total_requests,
            COALESCE(SUM(tokens_in), 0) AS total_tokens_in,
            COALESCE(SUM(tokens_out), 0) AS total_tokens_out,
            COALESCE(SUM(cost_usd), 0.0) AS total_cost_usd,
            COALESCE(AVG(latency_ms), 0) AS avg_latency_ms,
            COALESCE(AVG(CASE WHEN cache_hit THEN 1.0 ELSE 0.0 END), 0.0) AS cache_hit_rate
        FROM requests
        WHERE tenant_id = %s
    """
    print(f"\n sql ran \n")
    try:
        with psycopg.connect(settings.postgres_url) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (tenant_id,))
                row = cur.fetchone()
                
    except Exception as e:
        logger.warning("metrics.tenant_aggregates failed: %s", e)
        return {
            "tenant_id": tenant_id, "total_requests":0, "total_token_in":0,
            "total_token_out":0, "total_cost_usd":0.0, "avg_latency_ms": 0,
            "cache_hit_rate": 0.0,
        }
        
    total, tin, tout, cost, lat, hit = row
    
    return{
        "tenant_id": tenant_id, 
        "total_requests":int(total), 
        "total_token_in":int(tin),
        "total_token_out":int(tout), 
        "total_cost_usd":float(cost), 
        "avg_latency_ms": float(lat),
        "cache_hit_rate": float(hit),
    }
        
        
        
        
        
        
        
        
        
        
        
        
        
                
    
        