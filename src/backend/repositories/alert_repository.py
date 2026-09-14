"""
Repository layer for persisting and retrieving alerts and upload records.
Provides a clean abstraction over raw SQLAlchemy sessions, supporting bulk inserts
and standard CRUD operations.
"""

import uuid
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database.models import Upload, Alert


class AlertRepository:
    """Encapsulates database interactions for Upload and Alert entities.

    All methods expect an active SQLAlchemy ``Session`` which can be provided via
    the FastAPI ``Depends(get_db)`` dependency or instantiated manually in tests.
    """

    def __init__(self, db: Session):
        self.db = db

    # ---------------------------------------------------------------------
    # Upload operations
    # ---------------------------------------------------------------------
    def create_upload(self, file_name: str, file_path: str, user_id: Optional[UUID] = None) -> Upload:
        """Create a new ``Upload`` record and return the persisted instance.

        Args:
            file_name: Original filename supplied by the user.
            file_path: Relative path on the server where the file is stored.
            user_id: Owner user account UUID.
        """
        new_upload = Upload(file_name=file_name, file_path=file_path, user_id=user_id)
        self.db.add(new_upload)
        try:
            self.db.commit()
            self.db.refresh(new_upload)
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise RuntimeError(f"Failed to create upload record: {exc}")
        return new_upload

    def delete_upload(self, upload_id: UUID) -> None:
        """Delete an ``Upload`` and cascade‑delete its alerts.

        Raises:
            ValueError: If the upload does not exist.
        """
        upload = self.db.get(Upload, upload_id)
        if not upload:
            raise ValueError(f"Upload with id {upload_id} not found")
        self.db.delete(upload)
        try:
            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise RuntimeError(f"Failed to delete upload {upload_id}: {exc}")

    def get_upload(self, upload_id: UUID) -> Optional[Upload]:
        """Retrieve an ``Upload`` by its primary key."""
        return self.db.get(Upload, upload_id)

    # ---------------------------------------------------------------------
    # Alert operations
    # ---------------------------------------------------------------------
    def bulk_insert_alerts(self, upload_id: UUID, alerts: List[Alert], user_id: Optional[UUID] = None) -> int:
        """Bulk‑insert a list of ``Alert`` objects linked to *upload_id*.

        The method validates that the parent ``Upload`` exists before insertion.
        Returns the number of rows inserted.
        """
        # Ensure parent upload exists
        parent = self.db.get(Upload, upload_id)
        if not parent:
            raise ValueError(f"Upload with id {upload_id} not found for bulk insert")

        uid = user_id or getattr(parent, "user_id", None)

        # Attach foreign keys to each alert instance (in‑place mutation)
        for alert in alerts:
            alert.upload_id = upload_id
            if uid and not getattr(alert, "user_id", None):
                alert.user_id = uid

        # Use SQLAlchemy's bulk_save_objects for performance
        self.db.bulk_save_objects(alerts)
        try:
            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise RuntimeError(f"Bulk insert of alerts failed: {exc}")
        return len(alerts)

    def get_alert_by_id(self, alert_id: UUID) -> Optional[Alert]:
        """Fetch a single ``Alert`` by its primary key."""
        return self.db.get(Alert, alert_id)

    def get_alerts_by_upload(
        self,
        upload_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Alert]:
        """Return alerts belonging to *upload_id* with pagination support."""
        query = (
            self.db.query(Alert)
            .filter(Alert.upload_id == upload_id)
            .order_by(Alert.timestamp)
            .limit(limit)
            .offset(offset)
        )
        return query.all()

    def count_alerts(self) -> int:
        """Return the total number of alert rows stored in the database."""
        return self.db.query(Alert).count()

    def delete_alert(self, alert_id: UUID) -> None:
        """Delete a single alert by its primary key.

        Raises:
            ValueError: If the alert does not exist.
        """
        alert = self.db.get(Alert, alert_id)
        if not alert:
            raise ValueError(f"Alert with id {alert_id} not found")
        self.db.delete(alert)
        try:
            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise RuntimeError(f"Failed to delete alert {alert_id}: {exc}")
