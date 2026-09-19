"""Add streaming-ingestion persistence tables and alert idempotency fields."""

from alembic import op
import sqlalchemy as sa

revision = "001_streaming_ingestion"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    alert_columns = {column["name"] for column in inspector.get_columns("alerts")}
    for name, column in {
        "source": sa.Column("source", sa.String(80), nullable=False, server_default="csv"),
        "dedupe_hash": sa.Column("dedupe_hash", sa.String(64), nullable=True),
    }.items():
        if name not in alert_columns:
            op.add_column("alerts", column)
    op.create_index("ix_alerts_dedupe_hash", "alerts", ["dedupe_hash"], unique=True)

    chain_columns = {column["name"] for column in inspector.get_columns("attack_chains")}
    additions = [
        ("status", sa.String(20), "open"), ("first_seen", sa.DateTime(timezone=True), None),
        ("last_seen", sa.DateTime(timezone=True), None), ("event_counts", sa.Text(), None),
        ("risk_score_value", sa.Integer(), None), ("tier", sa.String(50), None),
        ("bluf_json", sa.Text(), None), ("playbook_json", sa.Text(), None),
        ("last_llm_run", sa.DateTime(timezone=True), None),
    ]
    for name, type_, default in additions:
        if name not in chain_columns:
            kwargs = {"nullable": True}
            if default is not None:
                kwargs["server_default"] = default
                kwargs["nullable"] = False
            op.add_column("attack_chains", sa.Column(name, type_, **kwargs))

    op.create_table(
        "dead_letters",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("source", sa.String(80), nullable=False), sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("error", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "connectors",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("type", sa.String(80), nullable=False), sa.Column("config", sa.Text(), nullable=False),
        sa.Column("cursor", sa.Text()), sa.Column("status", sa.String(30), nullable=False),
        sa.Column("last_sync", sa.DateTime(timezone=True)), sa.Column("events_ingested", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "api_keys",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(120), nullable=False), sa.Column("key_hash", sa.String(128), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("last_used_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    op.drop_table("api_keys")
    op.drop_table("connectors")
    op.drop_table("dead_letters")
