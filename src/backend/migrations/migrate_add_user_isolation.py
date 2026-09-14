"""
Database Migration: Add user_id foreign keys and user isolation to uploads, alerts, attack_chains, and chat_history.
Ensures existing records are backfilled to the primary analyst account.
"""

import os
import sys
import uuid
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(env_path)

db_url = os.getenv("DATABASE_URL", "").strip('"\'')
if not db_url:
    print("[ERROR] DATABASE_URL not set in environment.")
    sys.exit(1)

if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

print(f"[MIGRATION] Connecting to database...")
engine = create_engine(db_url)

DEFAULT_EMAIL = "analyst@sentinelforge.mil"
DEFAULT_USER_ID = "11111111-1111-1111-1111-111111111111"

with engine.connect() as conn:
    print("[1/5] Ensuring seed analyst user exists...")
    # Check if seed user exists
    user_row = conn.execute(
        text("SELECT id FROM users WHERE email = :email"),
        {"email": DEFAULT_EMAIL}
    ).fetchone()

    if user_row:
        seed_user_id = str(user_row[0])
        print(f"  -> Found existing seed user: {seed_user_id}")
    else:
        # Check if ANY user exists
        any_user = conn.execute(text("SELECT id FROM users LIMIT 1")).fetchone()
        if any_user:
            seed_user_id = str(any_user[0])
            print(f"  -> Using first existing user as seed: {seed_user_id}")
        else:
            # Create seed user
            seed_user_id = DEFAULT_USER_ID
            # PBKDF2 hash for 'SentinelForge#2026'
            sample_hash = "pbkdf2:sha256:100000$67b93a0bfa254921$84e868a8677c72449a03cf69c76082c3c6314c45b736b7617fa7259ea62bf9f7"
            conn.execute(
                text("""
                    INSERT INTO users (id, email, hashed_password, full_name, created_at)
                    VALUES (:id, :email, :password, :name, NOW())
                    ON CONFLICT (email) DO NOTHING;
                """),
                {
                    "id": seed_user_id,
                    "email": DEFAULT_EMAIL,
                    "password": sample_hash,
                    "name": "Chief SOC Analyst",
                }
            )
            conn.commit()
            print(f"  -> Created seed user with ID: {seed_user_id}")

    print(f"[2/5] Updating 'uploads' table...")
    # Check if user_id column exists on uploads
    col_exists = conn.execute(
        text("""
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'uploads' AND column_name = 'user_id';
        """)
    ).fetchone()

    if not col_exists:
        conn.execute(text("ALTER TABLE uploads ADD COLUMN user_id UUID;"))
        conn.execute(
            text("UPDATE uploads SET user_id = :uid WHERE user_id IS NULL;"),
            {"uid": seed_user_id}
        )
        conn.execute(text("ALTER TABLE uploads ALTER COLUMN user_id SET NOT NULL;"))
        conn.execute(text("""
            ALTER TABLE uploads 
            ADD CONSTRAINT fk_uploads_user_id 
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_uploads_user_id ON uploads(user_id);"))
        conn.commit()
        print("  -> Added user_id to uploads and indexed.")
    else:
        print("  -> Column user_id already exists on uploads.")

    print(f"[3/5] Updating 'alerts' table...")
    col_exists = conn.execute(
        text("""
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'alerts' AND column_name = 'user_id';
        """)
    ).fetchone()

    if not col_exists:
        conn.execute(text("ALTER TABLE alerts ADD COLUMN user_id UUID;"))
        # Backfill from uploads
        conn.execute(text("""
            UPDATE alerts a 
            SET user_id = u.user_id 
            FROM uploads u 
            WHERE a.upload_id = u.id AND a.user_id IS NULL;
        """))
        # Fallback for any orphan alert
        conn.execute(
            text("UPDATE alerts SET user_id = :uid WHERE user_id IS NULL;"),
            {"uid": seed_user_id}
        )
        conn.execute(text("ALTER TABLE alerts ALTER COLUMN user_id SET NOT NULL;"))
        conn.execute(text("""
            ALTER TABLE alerts 
            ADD CONSTRAINT fk_alerts_user_id 
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_alerts_user_id ON alerts(user_id);"))
        conn.commit()
        print("  -> Added user_id to alerts and indexed.")
    else:
        print("  -> Column user_id already exists on alerts.")

    print(f"[4/5] Updating 'attack_chains' table...")
    col_exists = conn.execute(
        text("""
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'attack_chains' AND column_name = 'user_id';
        """)
    ).fetchone()

    if not col_exists:
        conn.execute(text("ALTER TABLE attack_chains ADD COLUMN user_id UUID;"))
        conn.execute(
            text("UPDATE attack_chains SET user_id = :uid WHERE user_id IS NULL;"),
            {"uid": seed_user_id}
        )
        conn.execute(text("ALTER TABLE attack_chains ALTER COLUMN user_id SET NOT NULL;"))
        conn.execute(text("""
            ALTER TABLE attack_chains 
            ADD CONSTRAINT fk_attack_chains_user_id 
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_attack_chains_user_id ON attack_chains(user_id);"))
        
        # Drop global unique constraint on chain_id if present
        try:
            conn.execute(text("ALTER TABLE attack_chains DROP CONSTRAINT IF EXISTS attack_chains_chain_id_key;"))
        except Exception:
            pass
        try:
            conn.execute(text("DROP INDEX IF EXISTS attack_chains_chain_id_key;"))
        except Exception:
            pass

        # Create composite unique index
        conn.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS ix_attack_chains_user_chain 
            ON attack_chains(user_id, chain_id);
        """))
        conn.commit()
        print("  -> Added user_id to attack_chains with composite unique index.")
    else:
        print("  -> Column user_id already exists on attack_chains.")

    print(f"[5/5] Updating 'chat_history' table...")
    col_exists = conn.execute(
        text("""
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'chat_history' AND column_name = 'user_id';
        """)
    ).fetchone()

    if not col_exists:
        conn.execute(text("ALTER TABLE chat_history ADD COLUMN user_id UUID;"))
        conn.execute(text("""
            ALTER TABLE chat_history 
            ADD CONSTRAINT fk_chat_history_user_id 
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_chat_history_user_id ON chat_history(user_id);"))
        conn.commit()
        print("  -> Added user_id to chat_history and indexed.")
    else:
        print("  -> Column user_id already exists on chat_history.")

print("\n[SUCCESS] Multi-Tenant User Isolation migration completed successfully!")
