from pathlib import Path
import sys
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from services.json_parser import JSONAlertParser, JSONParserError

def alert(**overrides):
    value = {"timestamp": "2026-09-19T10:00:00Z", "src_ip": "45.20.10.5", "dst_ip": "10.0.0.5", "event_type": "PORT_SCAN", "severity": "MEDIUM"}
    value.update(overrides)
    return value

def test_parses_array_and_normalizes_event():
    result = JSONAlertParser().parse_payload([alert()], "json")
    assert result["valid_rows"] == 1
    assert result["alerts"][0].event == "PortScan"
    assert result["alerts"][0].source_type == "json"

def test_parses_common_wrappers():
    parser = JSONAlertParser()
    assert parser.parse_payload({"alerts": [alert()]}, "api")["valid_rows"] == 1
    assert parser.parse_payload({"data": [alert()]}, "api")["valid_rows"] == 1

@pytest.mark.parametrize("payload", [[], {"alerts": []}, {"wrong": []}])
def test_rejects_empty_or_unknown_wrapper(payload):
    with pytest.raises(JSONParserError): JSONAlertParser().parse_payload(payload, "json")

def test_rejects_invalid_json_and_missing_required_fields():
    with pytest.raises(JSONParserError, match="Invalid JSON"): JSONAlertParser().parse_bytes(b"{", "json")
    with pytest.raises(JSONParserError, match="missing required field"): JSONAlertParser().parse_payload([alert(src_ip="")], "json")
