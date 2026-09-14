"""
Unit and Integration tests for Enterprise Authentication Router (/api/v1/auth).
Tests registration, login, token verification, password reset, and profile inspection.
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import sys

# Ensure backend root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from main import app

import uuid

client = TestClient(app)

TEST_USER_EMAIL = f"soc.lead.{uuid.uuid4().hex[:6]}@threatintel.defense"
TEST_USER_PASS = "EnterprisePass#2026"
TEST_USER_NAME = "Commander Shepard"


def test_auth_register_success():
    """Test successful operator registration."""
    payload = {
        "name": TEST_USER_NAME,
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASS,
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == TEST_USER_EMAIL
    assert data["user"]["name"] == TEST_USER_NAME


def test_auth_register_duplicate_email():
    """Test duplicate registration returns 400."""
    payload = {
        "name": "Another Operator",
        "email": TEST_USER_EMAIL,
        "password": "Password1234#",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()


def test_auth_login_success():
    """Test valid login returns access token and user info."""
    payload = {
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASS,
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == TEST_USER_EMAIL


def test_auth_login_invalid_password():
    """Test invalid password returns 401 Unauthorized."""
    payload = {
        "email": TEST_USER_EMAIL,
        "password": "WrongPassword123#",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401


def test_auth_login_nonexistent_user():
    """Test nonexistent email returns 401."""
    payload = {
        "email": "ghost@doesnotexist.mil",
        "password": "SomePassword#123",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401


def test_auth_get_me():
    """Test retrieving current user profile using JWT token."""
    login_res = client.post("/api/v1/auth/login", json={
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASS,
    })
    token = login_res.json()["access_token"]

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == TEST_USER_EMAIL
    assert data["name"] == TEST_USER_NAME


def test_auth_forgot_and_reset_password():
    """Test forgot password issuance and reset verification."""
    # 1. Forgot password
    forgot_res = client.post("/api/v1/auth/forgot-password", json={"email": TEST_USER_EMAIL})
    assert forgot_res.status_code == 200
    reset_token = forgot_res.json()["reset_token_demo"]
    assert reset_token is not None

    # 2. Reset password
    NEW_PASS = "BrandNewPass#2026"
    reset_res = client.post("/api/v1/auth/reset-password", json={
        "token": reset_token,
        "new_password": NEW_PASS,
    })
    assert reset_res.status_code == 200
    assert reset_res.json()["status"] == "success"

    # 3. Verify login works with new password
    login_res = client.post("/api/v1/auth/login", json={
        "email": TEST_USER_EMAIL,
        "password": NEW_PASS,
    })
    assert login_res.status_code == 200
