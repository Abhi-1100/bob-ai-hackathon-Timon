"""
Database Migration: Add Behavioral Analysis tables and columns.
- Creates entity_baselines table
- Creates behavioral_analyses table
- Adds behavioral_score and behavioral_level columns to risk_scores table
Compatible with both PostgreSQL and SQLite.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

# Load environment variables
root_env = backend_dir.parent.parent / ".env"
curr_env = backend_dir / ".env"
if root_env.exists():
    load_dotenv(root_env)
elif curr_env.exists():
    load_dotenv(curr_env)
else:
    load_dotenv()

from database.models import Base
from database.session import _get_engine

def run_migration():
    print("[MIGRATION] Running Behavioral Analysis database migration...")
    engine = _get_engine()
    
    # 1. Create any missing tables (entity_baselines, behavioral_analyses)
    print("  -> Creating missing tables via SQLAlchemy metadata...")
    Base.metadata.create_all(bind=engine)
    print("  -> Base tables verified/created.")

    # 2. Check risk_scores table columns
    with engine.connect() as conn:
        inspector = inspect(engine)
        columns = [c["name"] for c in inspector.get_columns("risk_scores")]
        
        if "behavioral_score" not in columns:
            print("  -> Adding 'behavioral_score' column to risk_scores...")
            conn.execute(text("ALTER TABLE risk_scores ADD COLUMN behavioral_score INTEGER;"))
            conn.commit()
            print("     Added 'behavioral_score'.")
        else:
            print("  -> 'behavioral_score' already exists on risk_scores.")

        if "behavioral_level" not in columns:
            print("  -> Adding 'behavioral_level' column to risk_scores...")
            conn.execute(text("ALTER TABLE risk_scores ADD COLUMN behavioral_level VARCHAR(50);"))
            conn.commit()
            print("     Added 'behavioral_level'.")
        else:
            print("  -> 'behavioral_level' already exists on risk_scores.")

        # 3. Check behavioral_analyses table columns
        ba_columns = [c["name"] for c in inspector.get_columns("behavioral_analyses")]
        if "behavior_status" not in ba_columns:
            print("  -> Adding 'behavior_status' column to behavioral_analyses...")
            conn.execute(text("ALTER TABLE behavioral_analyses ADD COLUMN behavior_status VARCHAR(50);"))
            conn.commit()
            print("     Added 'behavior_status'.")

        if "context_tags" not in ba_columns:
            print("  -> Adding 'context_tags' column to behavioral_analyses...")
            conn.execute(text("ALTER TABLE behavioral_analyses ADD COLUMN context_tags TEXT;"))
            conn.commit()
            print("     Added 'context_tags'.")

        if "analyst_disposition" not in ba_columns:
            print("  -> Adding 'analyst_disposition' column to behavioral_analyses...")
            conn.execute(text("ALTER TABLE behavioral_analyses ADD COLUMN analyst_disposition VARCHAR(50) DEFAULT 'NEEDS_REVIEW';"))
            conn.commit()
            print("     Added 'analyst_disposition'.")

    print("[MIGRATION] Behavioral Analysis migration completed successfully!")

if __name__ == "__main__":
    run_migration()

