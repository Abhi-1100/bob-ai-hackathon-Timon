"""One-time PostgreSQL migration to label legacy alerts as CSV and add source provenance."""

import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv(Path(__file__).resolve().parents[3] / ".env")
db_url = os.getenv("DATABASE_URL", "").strip("\"'")
if not db_url:
    raise SystemExit("DATABASE_URL not set")
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

with create_engine(db_url).begin() as conn:
    exists = conn.execute(text("""SELECT 1 FROM information_schema.columns
        WHERE table_name = 'alerts' AND column_name = 'source_type'""")).fetchone()
    if not exists:
        conn.execute(text("ALTER TABLE alerts ADD COLUMN source_type VARCHAR(20) NOT NULL DEFAULT 'csv'"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_alerts_source_type ON alerts(source_type)"))
print("Alert source_type migration completed.")
