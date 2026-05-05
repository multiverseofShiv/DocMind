from fastapi import APIRouter, Depends

from app.core.security import verify_api_key
from app.services.metrics import tenant_aggregates


router = APIRouter()

@router.get("/metrics")
def metrics(tenant_id: str = Depends(verify_api_key)) -> dict:
    return tenant_aggregates(tenant_id)
    