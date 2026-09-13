"""
Unit and Integration tests for the CSV File Upload endpoint and storage service.
"""

import io
import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure backend root is on Python path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from main import app
from services.file_storage import BASE_DIR, UPLOADS_DIR

client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_uploaded_test_files():
    """Ensure clean uploads directory before and after tests."""
    yield
    # Cleanup any test artifacts created during tests
    if UPLOADS_DIR.exists():
        for file in UPLOADS_DIR.glob("alerts_*.csv"):
            try:
                file.unlink()
            except Exception:
                pass


def test_upload_valid_csv():
    """Test successful upload of a standard CSV file."""
    csv_content = b"alert_id,source,timestamp,severity,description\n1,SIEM,2026-09-13T10:00:00Z,CRITICAL,Port scan detected"
    files = {"file": ("test_alerts.csv", io.BytesIO(csv_content), "text/csv")}

    response = client.post("/api/v1/upload", files=files)
    assert response.status_code == 201

    data = response.json()
    assert data["success"] is True
    assert data["message"] == "File uploaded successfully"
    assert data["file_name"].startswith("alerts_")
    assert data["file_name"].endswith(".csv")
    assert data["file_path"] == f"uploads/{data['file_name']}"

    # Verify physical file existence and content preserved without parsing
    saved_file = BASE_DIR / data["file_path"]
    assert saved_file.exists()
    assert saved_file.read_bytes() == csv_content


def test_reject_non_csv_txt():
    """Test rejection of text (.txt) file."""
    txt_content = b"This is a raw log file, not a CSV."
    files = {"file": ("intel_report.txt", io.BytesIO(txt_content), "text/plain")}

    response = client.post("/api/v1/upload", files=files)
    assert response.status_code == 400

    data = response.json()
    assert data["success"] is False
    assert data["message"] == "Only CSV files are allowed"


def test_reject_non_csv_json():
    """Test rejection of JSON (.json) file."""
    json_content = b'{"alert_id": "A101", "severity": "HIGH"}'
    files = {"file": ("alerts.json", io.BytesIO(json_content), "application/json")}

    response = client.post("/api/v1/upload", files=files)
    assert response.status_code == 400

    data = response.json()
    assert data["success"] is False
    assert data["message"] == "Only CSV files are allowed"


def test_reject_non_csv_pdf():
    """Test rejection of PDF (.pdf) file."""
    pdf_content = b"%PDF-1.4 dummy content"
    files = {"file": ("threat_dossier.pdf", io.BytesIO(pdf_content), "application/pdf")}

    response = client.post("/api/v1/upload", files=files)
    assert response.status_code == 400

    data = response.json()
    assert data["success"] is False
    assert data["message"] == "Only CSV files are allowed"


def test_reject_empty_csv():
    """Test rejection of 0-byte empty CSV file."""
    empty_content = b""
    files = {"file": ("empty_alerts.csv", io.BytesIO(empty_content), "text/csv")}

    response = client.post("/api/v1/upload", files=files)
    assert response.status_code == 400

    data = response.json()
    assert data["success"] is False
    assert data["message"] == "Uploaded file is empty"
