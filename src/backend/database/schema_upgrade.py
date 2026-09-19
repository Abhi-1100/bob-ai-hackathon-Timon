"""Small additive bootstrap for deployments that still use ``create_all``.

Alembic remains the canonical migration path. This guard makes existing local
installations safe to start once while they migrate to the new revision.
"""

from sqlalchemy import inspect, text


def ensure_streaming_columns(engine) -> None:
    """Add streaming and behavioral analysis columns to pre-existing databases."""
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    statements = []

    if "alerts" in existing_tables:
        alert_columns = {column["name"] for column in inspector.get_columns("alerts")}
        if "source" not in alert_columns:
            statements.append("ALTER TABLE alerts ADD COLUMN source VARCHAR(80) NOT NULL DEFAULT 'csv'")
        if "dedupe_hash" not in alert_columns:
            statements.append("ALTER TABLE alerts ADD COLUMN dedupe_hash VARCHAR(64)")

    if "attack_chains" in existing_tables:
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

    if "risk_scores" in existing_tables:
        risk_columns = {column["name"] for column in inspector.get_columns("risk_scores")}
        if "behavioral_score" not in risk_columns:
            statements.append("ALTER TABLE risk_scores ADD COLUMN behavioral_score INTEGER")
        if "behavioral_level" not in risk_columns:
            statements.append("ALTER TABLE risk_scores ADD COLUMN behavioral_level VARCHAR(50)")

    if "behavioral_analyses" in existing_tables:
        ba_columns = {column["name"] for column in inspector.get_columns("behavioral_analyses")}
        if "behavior_status" not in ba_columns:
            statements.append("ALTER TABLE behavioral_analyses ADD COLUMN behavior_status VARCHAR(50)")
        if "context_tags" not in ba_columns:
            statements.append("ALTER TABLE behavioral_analyses ADD COLUMN context_tags TEXT")
        if "analyst_disposition" not in ba_columns:
            statements.append("ALTER TABLE behavioral_analyses ADD COLUMN analyst_disposition VARCHAR(50) DEFAULT 'NEEDS_REVIEW'")

    if not statements:
        return
    with engine.begin() as connection:
        for statement in statements:
            try:
                connection.execute(text(statement))
            except Exception:
                pass
        try:
            connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_alerts_dedupe_hash ON alerts (dedupe_hash)"))
        except Exception:
            pass
