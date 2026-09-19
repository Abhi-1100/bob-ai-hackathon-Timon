"""Small additive bootstrap for deployments that still use ``create_all``.

Alembic remains the canonical migration path. This guard makes existing local
installations safe to start once while they migrate to the new revision.
"""

from sqlalchemy import inspect, text


def ensure_streaming_columns(engine) -> None:
    """Add Phase 1 columns to pre-existing databases without changing data."""
    inspector = inspect(engine)
    statements = []
    alert_columns = {column["name"] for column in inspector.get_columns("alerts")}
    if "source" not in alert_columns:
        statements.append("ALTER TABLE alerts ADD COLUMN source VARCHAR(80) NOT NULL DEFAULT 'csv'")
    if "dedupe_hash" not in alert_columns:
        statements.append("ALTER TABLE alerts ADD COLUMN dedupe_hash VARCHAR(64)")

    chain_columns = {column["name"] for column in inspector.get_columns("attack_chains")}
    additions = {
        "status": "VARCHAR(20) DEFAULT 'open'",
        "first_seen": "TIMESTAMP",
        "last_seen": "TIMESTAMP",
        "event_counts": "TEXT",
        "risk_score_value": "INTEGER",
        "tier": "VARCHAR(50)",
        "bluf_json": "TEXT",
        "playbook_json": "TEXT",
        "last_llm_run": "TIMESTAMP",
    }
    for name, sql_type in additions.items():
        if name not in chain_columns:
            statements.append(f"ALTER TABLE attack_chains ADD COLUMN {name} {sql_type}")

    if not statements:
        return
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_alerts_dedupe_hash ON alerts (dedupe_hash)"))
