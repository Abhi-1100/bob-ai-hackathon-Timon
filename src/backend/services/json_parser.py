"""JSON alert parsing that produces the same canonical Alert objects as CSVParser."""

import json
import uuid
from typing import Any, Dict, List

from pydantic import ValidationError

from schemas.alert import Alert
from services.csv_parser import CSVParser


class JSONParserError(Exception):
    """A JSON feed is invalid, unsupported, or contains no usable alerts."""


class JSONAlertParser:
    """Normalize JSON arrays and common alert wrappers at the ingestion boundary."""

    REQUIRED_FIELDS = {"timestamp", "src_ip", "dst_ip", "event", "severity"}

    def extract_records(self, payload: Any) -> List[Dict[str, Any]]:
        if isinstance(payload, list):
            records = payload
        elif isinstance(payload, dict) and isinstance(payload.get("alerts"), list):
            records = payload["alerts"]
        elif isinstance(payload, dict) and isinstance(payload.get("data"), list):
            records = payload["data"]
        else:
            raise JSONParserError("JSON must be an alert array or an object containing 'alerts' or 'data'")
        if not records:
            raise JSONParserError("No alerts found")
        if not all(isinstance(record, dict) for record in records):
            raise JSONParserError("Each alert must be a JSON object")
        return records

    def parse_bytes(self, raw: bytes, source_type: str) -> Dict[str, Any]:
        try:
            payload = json.loads(raw.decode("utf-8"))
        except UnicodeDecodeError as exc:
            raise JSONParserError("JSON must be UTF-8 encoded") from exc
        except json.JSONDecodeError as exc:
            raise JSONParserError("Invalid JSON") from exc
        return self.parse_payload(payload, source_type)

    def parse_payload(self, payload: Any, source_type: str) -> Dict[str, Any]:
        records = self.extract_records(payload)
        alerts: List[Alert] = []
        errors: List[str] = []
        for index, record in enumerate(records, start=1):
            normalized = dict(record)
            # JSON/API commonly call this event_type; the canonical model calls it event.
            normalized.setdefault("event", normalized.get("event_type"))
            missing = sorted(field for field in self.REQUIRED_FIELDS if not normalized.get(field))
            if missing:
                errors.append(f"Alert {index}: missing required field(s): {', '.join(missing)}")
                continue
            normalized["event"] = CSVParser._normalize_event_name(normalized["event"])
            normalized["severity"] = CSVParser._normalize_severity(normalized["severity"])
            if not normalized["severity"]:
                errors.append(f"Alert {index}: invalid severity")
                continue
            metadata = {
                key: value for key, value in record.items()
                if key not in {"alert_id", "timestamp", "src_ip", "dst_ip", "event", "event_type", "severity"}
            }
            try:
                alerts.append(Alert(
                    alert_id=str(normalized.get("alert_id") or f"ALT-{uuid.uuid4().hex[:8].upper()}"),
                    timestamp=normalized["timestamp"], src_ip=str(normalized["src_ip"]),
                    dst_ip=str(normalized["dst_ip"]), event=normalized["event"], severity=normalized["severity"],
                    source_type=source_type, metadata=metadata,
                ))
            except ValidationError:
                errors.append(f"Alert {index}: schema validation failed")
        if not alerts:
            detail = errors[0] if errors else "No alerts found"
            raise JSONParserError(f"Alert schema validation failed: {detail}")
        return {"total_rows": len(records), "valid_rows": len(alerts), "invalid_rows": len(errors), "alerts": alerts, "errors": errors}
