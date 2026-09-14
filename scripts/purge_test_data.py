"""
Script to purge all test data from PostgreSQL and Qdrant Cloud.
Resets the environment so testing can start completely fresh from scratch.
"""
import os
import glob
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "src" / "backend"))

load_dotenv(BASE_DIR / ".env")

from sqlalchemy import create_engine, text
from qdrant_client import QdrantClient

def purge_all():
    print("=== 1. PURGING POSTGRESQL THREAT TELEMETRY & TEST ACCOUNTS ===")
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found!")
        return

    engine = create_engine(db_url)
    with engine.begin() as conn:
        for tbl in [
            "attack_chain_events",
            "mitre_mappings",
            "risk_scores",
            "recommendations",
            "reports",
            "attack_chains",
            "alerts",
            "uploads",
            "chat_history",
        ]:
            deleted = conn.execute(text(f"DELETE FROM {tbl};")).rowcount
            print(f"  - Deleted {deleted} rows from {tbl}")

        # Delete automated test users
        deleted_users = conn.execute(
            text("DELETE FROM users WHERE email LIKE 'isolation.test%' OR email LIKE 'soc.lead%';")
        ).rowcount
        print(f"  - Deleted {deleted_users} automated test user accounts from users")

        # Verify counts
        print("\nPostgreSQL Verification:")
        for tbl in ["users", "uploads", "alerts", "attack_chains", "chat_history"]:
            count = conn.execute(text(f"SELECT count(*) FROM {tbl};")).scalar()
            print(f"  - Current {tbl} row count: {count}")

    print("\n=== 2. PURGING QDRANT VECTOR DATABASE ===")
    q_url = os.getenv("QDRANT_URL")
    q_key = os.getenv("QDRANT_API_KEY")
    if q_url:
        client = QdrantClient(url=q_url, api_key=q_key)
        collections = client.get_collections()
        for c in collections.collections:
            print(f"  - Deleting Qdrant collection: {c.name}")
            client.delete_collection(c.name)
        print("  - Qdrant collection(s) deleted.")

        # Re-initialize collection fresh
        from services.qdrant_service import QdrantService
        q_svc = QdrantService()
        info = client.get_collection(q_svc.collection_name)
        print(f"  - Reinitialized fresh collection '{q_svc.collection_name}' with {info.points_count} points.")

    print("\n=== 3. PURGING LOCAL DISK UPLOADS ===")
    upload_dir = BASE_DIR / "src" / "backend" / "uploads"
    if upload_dir.exists():
        for f in glob.glob(str(upload_dir / "*.csv")):
            try:
                os.remove(f)
                print(f"  - Removed {os.path.basename(f)}")
            except Exception as e:
                print(f"  - Could not remove {f}: {e}")

    print("\n=== PURGE COMPLETE: SYSTEM READY FOR FRESH TESTING ===")

if __name__ == "__main__":
    purge_all()
