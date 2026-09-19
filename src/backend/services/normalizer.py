"""Source-agnostic alert normalization for streaming and batch ingestion."""

from __future__ import annotations

import hashlib
import ipaddress
import logging
import math
import re
from datetime import datetime, timezone
from typing import Any, Mapping, Optional

from pydantic import ValidationError

from schemas.alert import Alert

logger = logging.getLogger("alert_normalizer")

EVENT_NORMALIZATION_MAP = {
    "portscan": "PortScan", "port scan": "PortScan", "port_scan": "PortScan", "port-scan": "PortScan",
    "bruteforce": "BruteForce", "brute force": "BruteForce", "brute_force": "BruteForce",
    "ddos": "DDoS", "dos": "DoS", "sqlinjection": "SQLInjection", "sql injection": "SQLInjection", "sqli": "SQLInjection",
    "phishing": "Phishing", "phishing email": "Phishing", "malware": "Malware", "malware download": "MalwareDownload", "malware_download": "MalwareDownload",
    "command execution": "CommandExecution", "rce": "RemoteCodeExecution", "privilege escalation": "PrivilegeEscalation", "priv_esc": "PrivilegeEscalation",
    "data exfiltration": "DataExfiltration", "exfiltration": "DataExfiltration", "c2 beacon": "C2Beacon", "c2_beacon": "C2Beacon", "beaconing": "C2Beacon",
    "lateral movement": "LateralMovement", "credential dumping": "CredentialDumping", "unauthorized access": "UnauthorizedAccess",
}

FIELD_MAPS = {
    "generic": {"timestamp": "timestamp", "src_ip": "src_ip", "dst_ip": "dst_ip", "event": "event", "severity": "severity"},
    "wazuh": {"timestamp": "timestamp", "src_ip": "data.srcip", "dst_ip": "data.dstip", "event": "rule.description", "severity": "rule.level"},
    "suricata": {"timestamp": "timestamp", "src_ip": "src_ip", "dst_ip": "dest_ip", "event": "alert.signature", "severity": "alert.severity"},
}


class NormalizationError(ValueError):
    """Raised when a raw event cannot become a canonical alert."""


def nested_get(payload: Mapping[str, Any], path: str) -> Any:
    """Read a dotted field path from nested dictionaries."""
    value: Any = payload
    for part in path.split("."):
        if not isinstance(value, Mapping) or part not in value:
            return None
        value = value[part]
    return value


class AlertNormalizer:
    """Normalize generic, Wazuh, and Suricata records into ``Alert`` models."""

    def __init__(self, source: str = "generic") -> None:
        source_key = source.lower().strip()
        if source_key not in FIELD_MAPS:
            raise ValueError(f"Unsupported alert source '{source}'")
        self.source = source_key
        self.field_map = FIELD_MAPS[source_key]

    @staticmethod
    def normalize_event(raw_event: Any) -> str:
        if raw_event is None or not str(raw_event).strip():
            raise NormalizationError("event is required")
        value = str(raw_event).strip()
        key = value.lower().replace("-", " ").replace("_", " ")
        if key in EVENT_NORMALIZATION_MAP:
            return EVENT_NORMALIZATION_MAP[key]
        compact = key.replace(" ", "")
        if compact in EVENT_NORMALIZATION_MAP:
            return EVENT_NORMALIZATION_MAP[compact]
        return "".join(token.capitalize() for token in re.split(r"[\s_-]+", value) if token)

    @staticmethod
    def normalize_severity(raw_severity: Any) -> str:
        if raw_severity is None or not str(raw_severity).strip():
            raise NormalizationError("severity is required")
        if isinstance(raw_severity, (int, float)) or str(raw_severity).strip().isdigit():
            level = float(raw_severity)
            if not math.isfinite(level):
                raise NormalizationError("severity must be finite")
            if level <= 3:
                return "Low"
            if level <= 7:
                return "Medium"
            if level <= 12:
                return "High"
            return "Critical"
        value = str(raw_severity).strip().lower()
        aliases = {"informational": "Low", "info": "Low", "warning": "Medium", "warn": "Medium", "error": "High", "fatal": "Critical"}
        normalized = aliases.get(value, value.capitalize())
        if normalized not in {"Low", "Medium", "High", "Critical"}:
            raise NormalizationError(f"unsupported severity '{raw_severity}'")
        return normalized

    @staticmethod
    def normalize_timestamp(raw_timestamp: Any) -> datetime:
        if raw_timestamp is None or not str(raw_timestamp).strip():
            raise NormalizationError("timestamp is required")
        value = str(raw_timestamp).strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError as exc:
            raise NormalizationError(f"invalid ISO-8601 timestamp '{raw_timestamp}'") from exc
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    @staticmethod
    def normalize_ip(value: Any, field: str) -> str:
        if value is None or not str(value).strip():
            raise NormalizationError(f"{field} is required")
        candidate = str(value).strip()
        try:
            return str(ipaddress.ip_address(candidate))
        except ValueError as exc:
            raise NormalizationError(f"invalid {field} '{candidate}'") from exc

    def normalize(self, raw_event: Mapping[str, Any]) -> Alert:
        """Normalize and validate one external record."""
        values = {field: nested_get(raw_event, path) for field, path in self.field_map.items()}
        try:
            alert = Alert(
                timestamp=self.normalize_timestamp(values["timestamp"]),
                src_ip=self.normalize_ip(values["src_ip"], "src_ip"),
                dst_ip=self.normalize_ip(values["dst_ip"], "dst_ip"),
                event=self.normalize_event(values["event"]),
                severity=self.normalize_severity(values["severity"]),
                metadata={"source": self.source},
            )
        except ValidationError as exc:
            raise NormalizationError(str(exc)) from exc
        return alert

    @staticmethod
    def dedupe_hash(user_id: Any, alert: Alert) -> str:
        """Return the stable tenant-scoped idempotency key for an alert."""
        value = "|".join((str(user_id), alert.timestamp.isoformat(), alert.src_ip, alert.dst_ip, alert.event))
        return hashlib.sha256(value.encode("utf-8")).hexdigest()
