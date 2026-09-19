"""One-shot script: adds source, dedupe_hash to alerts and new columns to attack_chains."""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[3] / ".env")
db_url = os.getenv("DATABASE_URL", "").strip("\"'")
if not db_url:
    raise SystemExit("DATABASE_URL not set")
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sqlalchemy import create_engine
from database.schema_upgrade import ensure_streaming_columns

engine = create_engine(db_url)
ensure_streaming_columns(engine)
print("✓ schema_upgrade: source, dedupe_hash, and attack_chains columns added/verified.")
