"""Tenant-scoped connector management API."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.models import ConnectorDB, UserDB
from database.session import get_db
from routers.auth import get_current_user_obj
from services.live_runtime import runtime

router = APIRouter(prefix="/api/v1/connectors", tags=["Data sources"])


class ConnectorCreateRequest(BaseModel):
    type: str = Field(..., pattern=r"^[A-Za-z0-9_-]{1,40}$")
    config: dict[str, Any] = Field(default_factory=dict)


def public_connector(record: ConnectorDB) -> dict[str, Any]:
    """Return connector state without returning configuration secrets."""
    config = json.loads(record.config or "{}")
    safe_config = {key: value for key, value in config.items() if "secret" not in key.lower() and "token" not in key.lower() and "password" not in key.lower() and "key" not in key.lower()}
    return {"id": str(record.id), "type": record.type, "config": safe_config, "status": record.status, "last_sync": record.last_sync.isoformat() if record.last_sync else None, "events_ingested": record.events_ingested}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_connector(request: ConnectorCreateRequest, current_user: UserDB = Depends(get_current_user_obj), db: Session = Depends(get_db)):
    record = ConnectorDB(user_id=current_user.id, type=request.type, config=json.dumps(request.config), status="disabled")
    db.add(record)
    db.commit()
    db.refresh(record)
    return public_connector(record)


@router.get("")
def list_connectors(current_user: UserDB = Depends(get_current_user_obj), db: Session = Depends(get_db)):
    return [public_connector(item) for item in db.query(ConnectorDB).filter(ConnectorDB.user_id == current_user.id).all()]


@router.post("/{connector_id}/enable")
async def enable_connector(connector_id: str, current_user: UserDB = Depends(get_current_user_obj), db: Session = Depends(get_db)):
    record = db.query(ConnectorDB).filter(ConnectorDB.id == uuid.UUID(connector_id), ConnectorDB.user_id == current_user.id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Connector not found")
    record.status = "enabled"
    db.commit()
    await runtime.start_connector(str(record.id), current_user.id, json.loads(record.config or "{}"), record.type)
    return public_connector(record)


@router.post("/{connector_id}/disable")
async def disable_connector(connector_id: str, current_user: UserDB = Depends(get_current_user_obj), db: Session = Depends(get_db)):
    record = db.query(ConnectorDB).filter(ConnectorDB.id == uuid.UUID(connector_id), ConnectorDB.user_id == current_user.id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Connector not found")
    record.status = "disabled"
    db.commit()
    await runtime.stop_connector(str(record.id))
    return public_connector(record)
