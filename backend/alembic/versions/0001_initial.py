"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-06-04
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

EMBEDDING_DIM = 384


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    def embedding_col() -> sa.Column:
        # pgvector on Postgres; JSON elsewhere (keeps the migration portable).
        if bind.dialect.name == "postgresql":
            return sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=False)
        return sa.Column("embedding", sa.JSON(), nullable=False)

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "profiles",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "seniority",
            sa.Enum("junior", "mid", "senior", name="profile_seniority"),
            nullable=False,
            server_default="mid",
        ),
        sa.Column(
            "preferred_modality",
            sa.Enum("remote", "hybrid", "onsite", "any", name="profile_modality"),
            nullable=False,
            server_default="any",
        ),
        sa.Column("preferred_location", sa.String(120), nullable=True),
        sa.Column("salary_expectation", sa.Integer(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", name="uq_profiles_user_id"),
    )
    op.create_index("ix_profiles_user_id", "profiles", ["user_id"])

    op.create_table(
        "skills",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("profile_id", sa.Uuid(), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        embedding_col(),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_skills_profile_id", "skills", ["profile_id"])

    op.create_table(
        "projects",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("profile_id", sa.Uuid(), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("tech", sa.JSON(), nullable=False),
        embedding_col(),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_projects_profile_id", "projects", ["profile_id"])

    op.create_table(
        "job_opportunities",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("profile_id", sa.Uuid(), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("link", sa.String(1000), nullable=True),
        sa.Column("company", sa.String(200), nullable=False),
        sa.Column("role_title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("stack", sa.JSON(), nullable=False),
        sa.Column("requirements", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "modality",
            sa.Enum("remote", "hybrid", "onsite", "unknown", name="job_modality"),
            nullable=False,
            server_default="unknown",
        ),
        sa.Column("country", sa.String(120), nullable=True),
        sa.Column("salary", sa.Integer(), nullable=True),
        embedding_col(),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_job_opportunities_profile_id", "job_opportunities", ["profile_id"])

    op.create_table(
        "scores",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "job_opportunity_id",
            sa.Uuid(),
            sa.ForeignKey("job_opportunities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column(
            "recommendation",
            sa.Enum("apply", "apply_if_quick", "skip", name="score_recommendation"),
            nullable=False,
        ),
        sa.Column("breakdown", sa.JSON(), nullable=False),
        sa.Column("narrative", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("job_opportunity_id", name="uq_scores_job_opportunity_id"),
    )
    op.create_index("ix_scores_job_opportunity_id", "scores", ["job_opportunity_id"])

    application_state = sa.Enum(
        "nueva",
        "evaluando",
        "postulado",
        "seguimiento",
        "entrevista",
        "rechazado",
        "oferta",
        name="application_state",
    )

    op.create_table(
        "applications",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "job_opportunity_id",
            sa.Uuid(),
            sa.ForeignKey("job_opportunities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("score_id", sa.Uuid(), sa.ForeignKey("scores.id", ondelete="SET NULL"), nullable=True),
        sa.Column("state", application_state, nullable=False, server_default="nueva"),
        sa.Column("next_action", sa.String(300), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("job_opportunity_id", name="uq_applications_job_opportunity_id"),
    )
    op.create_index("ix_applications_job_opportunity_id", "applications", ["job_opportunity_id"])

    op.create_table(
        "application_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "application_id",
            sa.Uuid(),
            sa.ForeignKey("applications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("actor", sa.String(120), nullable=False),
        # Reuse the existing application_state type (do not re-create it).
        sa.Column(
            "from_state",
            sa.Enum(name="application_state", create_type=False),
            nullable=True,
        ),
        sa.Column(
            "to_state",
            sa.Enum(name="application_state", create_type=False),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_application_events_application_id", "application_events", ["application_id"])

    op.create_table(
        "generated_messages",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "application_id",
            sa.Uuid(),
            sa.ForeignKey("applications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "type",
            sa.Enum("recruiter_outreach", name="message_type"),
            nullable=False,
            server_default="recruiter_outreach",
        ),
        sa.Column("tone", sa.String(60), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_generated_messages_application_id", "generated_messages", ["application_id"])


def downgrade() -> None:
    op.drop_table("generated_messages")
    op.drop_table("application_events")
    op.drop_table("applications")
    op.drop_table("scores")
    op.drop_table("job_opportunities")
    op.drop_table("projects")
    op.drop_table("skills")
    op.drop_table("profiles")
    op.drop_table("users")
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        for enum_name in (
            "message_type",
            "application_state",
            "score_recommendation",
            "job_modality",
            "profile_modality",
            "profile_seniority",
        ):
            op.execute(f"DROP TYPE IF EXISTS {enum_name}")
