"""Initial database tables."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001_core_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "patients",
        sa.Column("id", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("given_name", sa.String(length=120), nullable=True),
        sa.Column("family_name", sa.String(length=120), nullable=True),
        sa.Column("gender", sa.String(length=32), nullable=True),
        sa.Column("birth_date", sa.String(length=32), nullable=True),
        sa.Column("contact", sa.JSON(), nullable=True),
    )

    op.create_table(
        "encounters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("patient_id", sa.String(length=64), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "treatment_adjustments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("patient_id", sa.String(length=64), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("requested_by", sa.String(length=64), nullable=False),
        sa.Column("order_id", sa.String(length=64), nullable=True),
        sa.Column("field_path", sa.String(length=255), nullable=False),
        sa.Column("new_value", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'requested'")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "adjustment_decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("adjustment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("treatment_adjustments.id"), nullable=False, unique=True),
        sa.Column("decided_by", sa.String(length=64), nullable=False),
        sa.Column("decided_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
    )

    op.create_table(
        "adjustment_audit_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("adjustment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("treatment_adjustments.id"), nullable=False),
        sa.Column("actor_id", sa.String(length=64), nullable=False),
        sa.Column("actor_role", sa.String(length=32), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "observations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("patient_id", sa.String(length=64), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("unit", sa.String(length=32), nullable=True),
        sa.Column("value_text", sa.String(length=128), nullable=False),
        sa.Column("value_numeric", sa.Float(), nullable=True),
        sa.Column("effective_at", sa.DateTime(), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_observations_code", "observations", ["code"])
    op.create_index("ix_observations_effective_at", "observations", ["effective_at"])

    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("patient_id", sa.String(length=64), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("rule", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default=sa.text("'open'")),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("observed_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_index("ix_observations_effective_at", table_name="observations")
    op.drop_index("ix_observations_code", table_name="observations")
    op.drop_table("observations")
    op.drop_table("adjustment_audit_entries")
    op.drop_table("adjustment_decisions")
    op.drop_table("treatment_adjustments")
    op.drop_table("encounters")
    op.drop_table("patients")
