"""
Unit tests for CSVParser and Alert schema validation.
"""

import io
from pathlib import Path
import pytest

# Ensure backend root is on Python path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from schemas.alert import Alert, AlertSeverity
from services.csv_parser import CSVParser, CSVParserError


@pytest.fixture
def parser():
    return CSVParser()


def test_parse_valid_csv(parser):
    """Test full parsing of valid alerts."""
    csv_data = (
        "timestamp,src_ip,dst_ip,event,severity\n"
        "2026-09-13 10:01:00,10.0.0.1,10.0.0.5,PortScan,Medium\n"
        "2026-09-13 10:02:00,192.168.1.100,10.0.0.5,BruteForce,High\n"
    )
    result = parser.parse(io.StringIO(csv_data))

    assert result["total_rows"] == 2
    assert result["valid_rows"] == 2
    assert result["invalid_rows"] == 0
    assert len(result["alerts"]) == 2

    alert1 = result["alerts"][0]
    assert isinstance(alert1, Alert)
    assert alert1.src_ip == "10.0.0.1"
    assert alert1.dst_ip == "10.0.0.5"
    assert alert1.event == "PortScan"
    assert alert1.severity == "Medium"


def test_missing_required_column_raises_error(parser):
    """Test rejection when required column (severity) is missing."""
    csv_data = (
        "timestamp,src_ip,dst_ip,event\n"
        "2026-09-13 10:01:00,10.0.0.1,10.0.0.5,PortScan\n"
    )
    with pytest.raises(CSVParserError) as exc_info:
        parser.parse(io.StringIO(csv_data))
    assert "Missing required column(s): severity" in str(exc_info.value)


def test_empty_dataset_raises_error(parser):
    """Test rejection of empty CSV."""
    csv_data = "timestamp,src_ip,dst_ip,event,severity\n"
    with pytest.raises(CSVParserError) as exc_info:
        parser.parse(io.StringIO(csv_data))
    assert "at least 1 data row" in str(exc_info.value).lower()


def test_remove_duplicate_and_empty_rows(parser):
    """Test that duplicate and empty rows are removed."""
    csv_data = (
        "timestamp,src_ip,dst_ip,event,severity\n"
        "2026-09-13 10:01:00,10.0.0.1,10.0.0.5,PortScan,Medium\n"
        ",,,,\n"  # Completely empty row
        "2026-09-13 10:01:00,10.0.0.1,10.0.0.5,PortScan,Medium\n"  # Exact duplicate
        "2026-09-13 10:05:00,10.0.0.2,10.0.0.5,PortScan,Low\n"
    )
    result = parser.parse(io.StringIO(csv_data))

    assert result["total_rows"] == 4
    assert result["valid_rows"] == 2
    assert result["invalid_rows"] == 2
    assert len(result["alerts"]) == 2


def test_whitespace_trimming(parser):
    """Test trimming of leading/trailing whitespace in cells."""
    csv_data = (
        "timestamp,src_ip,dst_ip,event,severity\n"
        "  2026-09-13 10:01:00  ,  10.0.0.1  ,  10.0.0.5  ,  PortScan  ,  Medium  \n"
    )
    result = parser.parse(io.StringIO(csv_data))

    assert result["valid_rows"] == 1
    alert = result["alerts"][0]
    assert alert.src_ip == "10.0.0.1"
    assert alert.dst_ip == "10.0.0.5"
    assert alert.event == "PortScan"
    assert alert.severity == "Medium"


def test_severity_normalization(parser):
    """Test normalization of critical, Critical, CRITICAL to 'Critical'."""
    csv_data = (
        "timestamp,src_ip,dst_ip,event,severity\n"
        "2026-09-13 10:01:00,10.0.0.1,10.0.0.5,PortScan,critical\n"
        "2026-09-13 10:02:00,10.0.0.2,10.0.0.5,PortScan,Critical\n"
        "2026-09-13 10:03:00,10.0.0.3,10.0.0.5,PortScan,CRITICAL\n"
        "2026-09-13 10:04:00,10.0.0.4,10.0.0.5,PortScan,InvalidSeverity\n"
    )
    result = parser.parse(io.StringIO(csv_data))

    assert result["total_rows"] == 4
    assert result["valid_rows"] == 3
    assert result["invalid_rows"] == 1  # InvalidSeverity skipped
    for a in result["alerts"]:
        assert a.severity == AlertSeverity.CRITICAL.value


def test_event_name_normalization(parser):
    """Test normalization of 'port scan', 'Port Scan', 'PORTSCAN' to 'PortScan'."""
    csv_data = (
        "timestamp,src_ip,dst_ip,event,severity\n"
        "2026-09-13 10:01:00,10.0.0.1,10.0.0.5,port scan,High\n"
        "2026-09-13 10:02:00,10.0.0.2,10.0.0.5,Port Scan,High\n"
        "2026-09-13 10:03:00,10.0.0.3,10.0.0.5,PORTSCAN,High\n"
    )
    result = parser.parse(io.StringIO(csv_data))

    assert result["valid_rows"] == 3
    for alert in result["alerts"]:
        assert alert.event == "PortScan"
