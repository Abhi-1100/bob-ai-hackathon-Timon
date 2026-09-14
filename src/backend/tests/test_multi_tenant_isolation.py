"""
Integration tests verifying strict multi-tenant user data isolation across the entire workflow:
1. New user gets an isolated empty workspace (0 alerts, 0 chains, 0 reports).
2. User A's data is never visible to User B.
3. User B ingests data, and only User B sees their new alerts and chains.
4. User B resets their workspace, leaving User A's alerts and chains untouched.
"""

import uuid
from pathlib import Path
import sys
import io
import pytest
from fastapi.testclient import TestClient

# Ensure backend root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from main import app
from database.session import _get_session_factory
from database.models import UserDB, Alert, AttackChainDB

client = TestClient(app)

SAMPLE_CSV = b"""timestamp,source,event,severity,src_ip,dst_ip
2026-03-10T10:00:00Z,Firewall,Port Scan,Low,198.51.100.55,10.0.0.10
2026-03-10T10:02:00Z,IDS,Brute Force SSH,Medium,198.51.100.55,10.0.0.10
2026-03-10T10:05:00Z,SIEM,Privilege Escalation,High,198.51.100.55,10.0.0.10
"""

def test_multi_tenant_isolation_end_to_end():
    db = _get_session_factory()()
    try:
        # Find seed user (User A)
        seed_user = db.query(UserDB).filter(UserDB.email == "analyst@sentinelforge.mil").first()
        if not seed_user:
            seed_user = db.query(UserDB).first()
        assert seed_user is not None, "Seed user should exist"

        # Count User A's existing data
        user_a_alerts_count = db.query(Alert).filter(Alert.user_id == seed_user.id).count()
        user_a_chains_count = db.query(AttackChainDB).filter(AttackChainDB.user_id == seed_user.id).count()
        print(f"\nUser A (Seed): {user_a_alerts_count} alerts, {user_a_chains_count} chains")

        # 1. Register a brand new operator (User B)
        user_b_email = f"isolation.test.{uuid.uuid4().hex[:6]}@defense.mil"
        reg_resp = client.post("/api/v1/auth/register", json={
            "name": "Cadet Investigator",
            "email": user_b_email,
            "password": "Password12345#",
        })
        assert reg_resp.status_code == 201, f"Registration failed: {reg_resp.text}"
        token_b = reg_resp.json()["access_token"]
        user_b_id = reg_resp.json()["user"]["id"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # 2. Verify User B starts with clean 0-state
        dash_b = client.get("/api/v1/dashboard/stats", headers=headers_b)
        assert dash_b.status_code == 200
        data_b = dash_b.json()
        assert data_b["total_alerts"] == 0, "New user should have 0 alerts"
        assert data_b["total_chains"] == 0, "New user should have 0 chains"
        assert len(data_b["recent_incidents"]) == 0

        chains_b = client.get("/api/v1/chains", headers=headers_b)
        assert chains_b.status_code == 200
        assert chains_b.json()["count"] == 0

        analytics_b = client.get("/api/v1/analytics/overview", headers=headers_b)
        assert analytics_b.status_code == 200
        assert analytics_b.json()["total_alerts"] == 0

        mitre_b = client.get("/api/v1/mitre/overview", headers=headers_b)
        assert mitre_b.status_code == 200
        assert mitre_b.json()["total_detected"] == 0

        reports_b = client.get("/api/v1/reports", headers=headers_b)
        assert reports_b.status_code == 200
        assert reports_b.json()["total_reports"] == 0

        # 3. User B ingests their own CSV file
        files = {"file": ("test_feed.csv", io.BytesIO(SAMPLE_CSV), "text/csv")}
        upload_resp = client.post("/api/v1/upload/ingest", files=files, headers=headers_b)
        assert upload_resp.status_code == 201, f"Upload failed: {upload_resp.text}"
        upload_data = upload_resp.json()
        assert upload_data["alerts_ingested"] == 3
        assert upload_data["chains_correlated"] >= 1

        # 4. Verify User B now sees ONLY their own data
        dash_b_after = client.get("/api/v1/dashboard/stats", headers=headers_b)
        assert dash_b_after.status_code == 200
        assert dash_b_after.json()["total_alerts"] == 3
        assert dash_b_after.json()["total_chains"] >= 1

        chains_b_after = client.get("/api/v1/chains", headers=headers_b)
        assert chains_b_after.status_code == 200
        assert chains_b_after.json()["count"] >= 1
        assert chains_b_after.json()["chains"][0]["source_ip"] == "198.51.100.55"

        # 5. Verify User A's data was NOT corrupted or modified by User B's actions
        user_a_alerts_after = db.query(Alert).filter(Alert.user_id == seed_user.id).count()
        user_a_chains_after = db.query(AttackChainDB).filter(AttackChainDB.user_id == seed_user.id).count()
        assert user_a_alerts_after == user_a_alerts_count, "User A alerts count changed!"
        assert user_a_chains_after == user_a_chains_count, "User A chains count changed!"

        # 6. User B resets their workspace
        reset_resp = client.post("/api/v1/dashboard/reset", headers=headers_b)
        assert reset_resp.status_code == 200

        # Verify User B is back to 0
        dash_b_reset = client.get("/api/v1/dashboard/stats", headers=headers_b)
        assert dash_b_reset.status_code == 200
        assert dash_b_reset.json()["total_alerts"] == 0
        assert dash_b_reset.json()["total_chains"] == 0

        # Verify User A's data is STILL intact!
        user_a_alerts_final = db.query(Alert).filter(Alert.user_id == seed_user.id).count()
        user_a_chains_final = db.query(AttackChainDB).filter(AttackChainDB.user_id == seed_user.id).count()
        assert user_a_alerts_final == user_a_alerts_count, "User A alerts should remain intact after User B reset"
        assert user_a_chains_final == user_a_chains_count, "User A chains should remain intact after User B reset"
        print("ALL MULTI-TENANT ISOLATION CHECKS PASSED!")

    finally:
        db.close()

if __name__ == "__main__":
    test_multi_tenant_isolation_end_to_end()
