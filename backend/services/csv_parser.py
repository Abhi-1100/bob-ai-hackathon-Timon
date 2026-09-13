"""
Production-Ready CSV Parser and Validation Service for Threat Intelligence Alerts.

Converts raw cybersecurity alert CSV files into validated, normalized Alert objects
ready for consumption by the Correlation Engine, Attack Chain Builder, and LangGraph Agents.
"""

import io
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import pandas as pd
from pydantic import ValidationError

from schemas.alert import Alert, AlertSeverity, ParseResult

logger = logging.getLogger("csv_parser")

# Required columns in the incoming alert CSV
REQUIRED_COLUMNS: Set[str] = {
    "timestamp",
    "src_ip",
    "dst_ip",
    "event",
    "severity",
}

# Standardized security event name normalization dictionary
EVENT_NORMALIZATION_MAP: Dict[str, str] = {
    "portscan": "PortScan",
    "port scan": "PortScan",
    "port_scan": "PortScan",
    "port-scan": "PortScan",
    "bruteforce": "BruteForce",
    "brute force": "BruteForce",
    "brute_force": "BruteForce",
    "ddos": "DDoS",
    "dos": "DoS",
    "sqlinjection": "SQLInjection",
    "sql injection": "SQLInjection",
    "sqli": "SQLInjection",
    "phishing": "Phishing",
    "phishing email": "Phishing",
    "malware": "Malware",
    "malware download": "MalwareDownload",
    "malware_download": "MalwareDownload",
    "command execution": "CommandExecution",
    "rce": "RemoteCodeExecution",
    "privilege escalation": "PrivilegeEscalation",
    "priv_esc": "PrivilegeEscalation",
    "data exfiltration": "DataExfiltration",
    "exfiltration": "DataExfiltration",
    "c2 beacon": "C2Beacon",
    "c2_beacon": "C2Beacon",
    "beaconing": "C2Beacon",
    "lateral movement": "LateralMovement",
    "credential dumping": "CredentialDumping",
    "unauthorized access": "UnauthorizedAccess",
}


class CSVParserError(Exception):
    """Raised when CSV structure is fundamentally invalid or unreadable."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class CSVParser:
    """
    Parser and validator for raw alert CSV data.
    Implements a modular multi-stage cleaning and normalization pipeline.
    """

    def __init__(self):
        self.required_columns = REQUIRED_COLUMNS

    def validate_columns(self, df: pd.DataFrame) -> None:
        """
        Validates that all mandatory columns exist in the DataFrame.
        Raises CSVParserError if any required column is missing.
        """
        # Normalize column names: strip whitespace and lowercase for comparison
        df.columns = df.columns.astype(str).str.strip().str.lower()
        existing_cols = set(df.columns)
        missing_cols = self.required_columns - existing_cols

        if missing_cols:
            error_msg = f"Missing required column(s): {', '.join(sorted(missing_cols))}"
            logger.error(f"Column validation failed: {error_msg}. Found columns: {list(df.columns)}")
            raise CSVParserError(error_msg)

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Cleans the DataFrame:
        - Drops rows where all fields are null/empty.
        - Trims whitespace from all string/object cells.
        - Removes duplicate rows across all required columns.
        """
        initial_count = len(df)

        # Drop completely empty rows
        df = df.dropna(how="all").copy()

        # Trim whitespace across all string columns
        for col in df.columns:
            if df[col].dtype == object or pd.api.types.is_string_dtype(df[col]):
                df[col] = df[col].astype(str).str.strip()
                # Replace string representations of nulls
                df[col] = df[col].replace(
                    {"nan": None, "None": None, "null": None, "": None}
                )

        # Drop rows that became completely null after whitespace stripping
        df = df.dropna(how="all", subset=list(self.required_columns)).copy()

        # Remove duplicate rows
        duplicates_count = df.duplicated(subset=list(self.required_columns)).sum()
        if duplicates_count > 0:
            logger.info(f"Removing {duplicates_count} duplicate alert rows")
            df = df.drop_duplicates(subset=list(self.required_columns)).reset_index(drop=True)

        cleaned_count = len(df)
        logger.debug(f"Data cleaning finished: {initial_count} -> {cleaned_count} rows")
        return df

    @staticmethod
    def _normalize_event_name(raw_event: Optional[str]) -> Optional[str]:
        """
        Normalizes event strings into standardized PascalCase names.
        Example: 'port scan', 'Port Scan', 'PORTSCAN' -> 'PortScan'
        """
        if not raw_event or pd.isna(raw_event):
            return None

        event_str = str(raw_event).strip()
        lookup_key = event_str.lower().replace("-", " ").replace("_", " ")

        # 1. Exact or normalized dictionary lookup
        if lookup_key in EVENT_NORMALIZATION_MAP:
            return EVENT_NORMALIZATION_MAP[lookup_key]

        # 2. Key with spaces stripped (handles 'portscan')
        lookup_compact = lookup_key.replace(" ", "")
        if lookup_compact in EVENT_NORMALIZATION_MAP:
            return EVENT_NORMALIZATION_MAP[lookup_compact]

        # 3. Dynamic PascalCase transformation
        # Split by spaces, underscores, hyphens
        tokens = re.split(r"[\s_\-]+", event_str)
        if len(tokens) > 1:
            return "".join(t.capitalize() for t in tokens if t)

        # Single word: if all uppercase and >= 4 letters, capitalize nicely
        if event_str.isupper():
            return event_str.capitalize()

        return event_str

    @staticmethod
    def _normalize_severity(raw_severity: Optional[str]) -> Optional[str]:
        """
        Normalizes severity string to Title case (Low, Medium, High, Critical).
        Returns None if invalid.
        """
        if not raw_severity or pd.isna(raw_severity):
            return None

        clean_sev = str(raw_severity).strip().capitalize()
        valid_severities = {s.value for s in AlertSeverity}

        if clean_sev in valid_severities:
            return clean_sev

        return None

    def normalize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Applies domain normalization:
        - Normalizes severity to Title case (Low, Medium, High, Critical).
        - Normalizes event names into PascalCase (e.g. 'port scan' -> 'PortScan').
        """
        df = df.copy()

        # Apply event normalization
        df["event"] = df["event"].apply(self._normalize_event_name)

        # Apply severity normalization
        df["severity"] = df["severity"].apply(self._normalize_severity)

        return df

    def parse_alerts(self, df: pd.DataFrame) -> Tuple[List[Alert], int]:
        """
        Iterates over normalized rows and converts valid records to Alert Pydantic models.
        Tracks invalid rows due to missing fields, invalid timestamps, or unknown severities.

        Returns:
            Tuple[List[Alert], int]: (valid_alerts, invalid_rows_count)
        """
        valid_alerts: List[Alert] = []
        invalid_count = 0

        for index, row in df.iterrows():
            row_num = index + 2  # Human-readable CSV row index (1-based + 1 for header)
            raw_timestamp = row.get("timestamp")
            src_ip = row.get("src_ip")
            dst_ip = row.get("dst_ip")
            event = row.get("event")
            severity = row.get("severity")

            # Check for critical missing values
            if not all([raw_timestamp, src_ip, dst_ip, event, severity]):
                logger.warning(
                    f"Validation error at row {row_num}: Missing required field values "
                    f"(timestamp='{raw_timestamp}', src_ip='{src_ip}', dst_ip='{dst_ip}', "
                    f"event='{event}', severity='{severity}')"
                )
                invalid_count += 1
                continue

            # Parse and validate timestamp
            parsed_dt = None
            try:
                # Use pandas flexible datetime parsing
                parsed_dt = pd.to_datetime(raw_timestamp).to_pydatetime()
            except Exception as dt_err:
                logger.warning(
                    f"Validation error at row {row_num}: Invalid timestamp format '{raw_timestamp}': {dt_err}"
                )
                invalid_count += 1
                continue

            # Attempt Pydantic model construction
            try:
                alert = Alert(
                    timestamp=parsed_dt,
                    src_ip=str(src_ip).strip(),
                    dst_ip=str(dst_ip).strip(),
                    event=str(event).strip(),
                    severity=severity,
                )
                valid_alerts.append(alert)
            except ValidationError as val_err:
                logger.warning(
                    f"Validation error at row {row_num}: Pydantic validation failed: {val_err}"
                )
                invalid_count += 1
            except Exception as exc:
                logger.warning(
                    f"Validation error at row {row_num}: Unexpected alert conversion error: {exc}"
                )
                invalid_count += 1

        return valid_alerts, invalid_count

    def parse(
        self,
        file_input: Union[str, Path, io.BytesIO, io.StringIO],
    ) -> Dict[str, Any]:
        """
        End-to-end pipeline method:
        1. Reads CSV safely into DataFrame.
        2. Validates column headers.
        3. Cleans whitespace, nulls, and duplicates.
        4. Normalizes events and severities.
        5. Converts rows into validated Alert models.
        6. Returns structured summary dictionary.

        Raises:
            CSVParserError: For unreadable files, missing columns, or 0 valid rows.
        """
        source_name = str(file_input) if isinstance(file_input, (str, Path)) else "memory_buffer"
        logger.info(f"CSV parsing started: source='{source_name}'")

        # 1. Load CSV into DataFrame
        try:
            df = pd.read_csv(file_input, dtype=str, skipinitialspace=True)
        except pd.errors.EmptyDataError:
            logger.error(f"CSV parsing failed: file '{source_name}' is empty")
            raise CSVParserError("CSV file is empty")
        except Exception as exc:
            logger.error(f"CSV parsing failed: Malformed CSV file '{source_name}': {exc}")
            raise CSVParserError(f"Malformed CSV: {str(exc)}")

        # 2. Check for empty dataset
        if df.empty:
            logger.error(f"CSV parsing failed: file '{source_name}' contains no data rows")
            raise CSVParserError("CSV must contain at least 1 data row")

        raw_total_rows = len(df)

        # 3. Validate columns
        self.validate_columns(df)

        # 4. Clean data (trim whitespace, drop null rows, drop duplicates)
        df_cleaned = self.clean_data(df)

        if df_cleaned.empty:
            logger.error(f"CSV parsing failed: All rows in '{source_name}' were empty or invalid")
            raise CSVParserError("CSV contains no valid non-empty data rows")

        # 5. Normalize data (event names and severity)
        df_normalized = self.normalize_data(df_cleaned)

        # 6. Parse into Alert models
        alerts, row_invalid_count = self.parse_alerts(df_normalized)

        # Calculate totals: invalid rows include dropped corrupt rows + rejected rows
        valid_rows = len(alerts)
        invalid_rows = (raw_total_rows - len(df_cleaned)) + row_invalid_count

        result = {
            "total_rows": raw_total_rows,
            "valid_rows": valid_rows,
            "invalid_rows": invalid_rows,
            "alerts": alerts,
        }

        logger.info(
            f"CSV parsing completed: total_rows={raw_total_rows}, "
            f"valid_rows={valid_rows}, invalid_rows={invalid_rows}"
        )

        return result
