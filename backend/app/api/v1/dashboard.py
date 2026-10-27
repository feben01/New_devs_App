from decimal import Decimal, ROUND_HALF_UP
from fastapi import APIRouter, Depends, HTTPException  # type: ignore[reportMissingImports]
from typing import Dict, Any
from app.services.cache import get_revenue_summary
from app.core.auth import authenticate_request as get_current_user

router = APIRouter()

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    property_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:

    tenant_id = getattr(current_user, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant could not be resolved")

    revenue_data = await get_revenue_summary(property_id, tenant_id)

    # Keep Decimal precision and round only once, at the end
    total = Decimal(str(revenue_data["total"])).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    return {
        "property_id": revenue_data["property_id"],
        "total_revenue": str(total),
        "currency": revenue_data["currency"],
        "reservations_count": revenue_data["count"],
    }