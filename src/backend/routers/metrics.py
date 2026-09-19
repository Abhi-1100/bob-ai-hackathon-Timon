"""Tenant-authenticated live processing metrics."""

from fastapi import APIRouter, Depends

from database.models import UserDB
from routers.auth import get_current_user_obj
from services.metrics import metrics

router = APIRouter(prefix="/api/v1/metrics", tags=["Metrics"])


@router.get("")
def get_live_metrics(current_user: UserDB = Depends(get_current_user_obj)):
    return metrics.snapshot()
