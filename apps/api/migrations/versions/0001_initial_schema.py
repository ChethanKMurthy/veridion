"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-10-09 18:15:31.093751
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("org_id", sa.String(length=40), nullable=True),
        sa.Column("actor_id", sa.String(length=40), nullable=True),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("entity_type", sa.String(length=40), nullable=True),
        sa.Column("entity_id", sa.String(length=40), nullable=True),
        sa.Column(
            "data",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("ip", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_events")),
    )
    with op.batch_alter_table("audit_events", schema=None) as batch_op:
        batch_op.create_index("ix_audit_events_org_created", ["org_id", "created_at"], unique=False)

    op.create_table(
        "enquiries",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("organization", sa.String(length=200), nullable=True),
        sa.Column("subject", sa.String(length=300), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "context",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_enquiries")),
    )
    with op.batch_alter_table("enquiries", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_enquiries_kind"), ["kind"], unique=False)

    op.create_table(
        "jobs",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("org_id", sa.String(length=40), nullable=True),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column(
            "payload",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("run_after", sa.DateTime(timezone=True), nullable=False),
        sa.Column("locked_by", sa.String(length=80), nullable=True),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "progress",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column(
            "result",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_jobs")),
    )
    with op.batch_alter_table("jobs", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_jobs_org_id"), ["org_id"], unique=False)
        batch_op.create_index("ix_jobs_status_run_after", ["status", "run_after"], unique=False)

    op.create_table(
        "llm_cache",
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=120), nullable=False),
        sa.Column("prompt_version", sa.String(length=40), nullable=False),
        sa.Column(
            "response",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column(
            "usage",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("key", name=op.f("pk_llm_cache")),
    )
    op.create_table(
        "organizations",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("plan", sa.String(length=32), nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_organizations")),
        sa.UniqueConstraint("slug", name=op.f("uq_organizations_slug")),
    )
    op.create_table(
        "requirement_sets",
        sa.Column("id", sa.String(length=120), nullable=False),
        sa.Column("key", sa.String(length=80), nullable=False),
        sa.Column("version", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("framework", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "standards",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("effective_rule", sa.Text(), nullable=True),
        sa.Column("review_status", sa.String(length=20), nullable=False),
        sa.Column(
            "changelog",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("supersedes", sa.String(length=120), nullable=True),
        sa.Column("succeeded_by", sa.String(length=120), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("loaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_requirement_sets")),
    )
    with op.batch_alter_table("requirement_sets", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_requirement_sets_key"), ["key"], unique=False)

    op.create_table(
        "users",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("password_hash", sa.String(length=300), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_table(
        "companies",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("org_id", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("industry", sa.String(length=120), nullable=True),
        sa.Column("country", sa.String(length=80), nullable=True),
        sa.Column("size_band", sa.String(length=40), nullable=True),
        sa.Column("fiscal_year_end", sa.String(length=5), nullable=False),
        sa.Column("website", sa.String(length=300), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_sample", sa.Boolean(), nullable=False),
        sa.Column("created_by", sa.String(length=40), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["org_id"],
            ["organizations.id"],
            name=op.f("fk_companies_org_id_organizations"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_companies")),
    )
    with op.batch_alter_table("companies", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_companies_org_id"), ["org_id"], unique=False)

    op.create_table(
        "memberships",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("org_id", sa.String(length=40), nullable=False),
        sa.Column("user_id", sa.String(length=40), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["org_id"],
            ["organizations.id"],
            name=op.f("fk_memberships_org_id_organizations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_memberships_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_memberships")),
        sa.UniqueConstraint("org_id", "user_id", name=op.f("uq_memberships_org_id")),
    )
    with op.batch_alter_table("memberships", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_memberships_org_id"), ["org_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_memberships_user_id"), ["user_id"], unique=False)

    op.create_table(
        "requirements",
        sa.Column("id", sa.String(length=160), nullable=False),
        sa.Column("set_id", sa.String(length=120), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("display_code", sa.String(length=60), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("topic", sa.String(length=80), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("applicability", sa.Text(), nullable=True),
        sa.Column("importance", sa.Integer(), nullable=False),
        sa.Column(
            "elements",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column(
            "metric_keys",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column(
            "search_terms",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column(
            "related_terms",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("source_reference", sa.String(length=300), nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(
            ["set_id"],
            ["requirement_sets.id"],
            name=op.f("fk_requirements_set_id_requirement_sets"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_requirements")),
    )
    with op.batch_alter_table("requirements", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_requirements_set_id"), ["set_id"], unique=False)

    op.create_table(
        "usage_events",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("org_id", sa.String(length=40), nullable=False),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("quantity", sa.Double(), nullable=False),
        sa.Column("ref_id", sa.String(length=40), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["org_id"],
            ["organizations.id"],
            name=op.f("fk_usage_events_org_id_organizations"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_usage_events")),
    )
    with op.batch_alter_table("usage_events", schema=None) as batch_op:
        batch_op.create_index(
            "ix_usage_events_org_kind_created", ["org_id", "kind", "created_at"], unique=False
        )

    op.create_table(
        "actions",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("org_id", sa.String(length=40), nullable=False),
        sa.Column("company_id", sa.String(length=40), nullable=False),
        sa.Column("finding_id", sa.String(length=40), nullable=True),
        sa.Column("run_id", sa.String(length=40), nullable=True),
        sa.Column("set_key", sa.String(length=80), nullable=True),
        sa.Column("requirement_code", sa.String(length=40), nullable=False),
        sa.Column("gap_key", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("owner", sa.String(length=200), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("effort", sa.String(length=10), nullable=False),
        sa.Column("priority_score", sa.Float(), nullable=False),
        sa.Column(
            "priority_components",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "depends_on",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("gap_closed_run_id", sa.String(length=40), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["company_id"], ["companies.id"], name=op.f("fk_actions_company_id_companies"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_actions")),
    )
    with op.batch_alter_table("actions", schema=None) as batch_op:
        batch_op.create_index(
            "ix_actions_company_gap", ["company_id", "requirement_code", "gap_key"], unique=False
        )
        batch_op.create_index(batch_op.f("ix_actions_org_id"), ["org_id"], unique=False)

    op.create_table(
        "applicability_decisions",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("org_id", sa.String(length=40), nullable=False),
        sa.Column("company_id", sa.String(length=40), nullable=False),
        sa.Column("set_key", sa.String(length=80), nullable=False),
        sa.Column("requirement_code", sa.String(length=40), nullable=False),
        sa.Column("applicable", sa.Boolean(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("decided_by", sa.String(length=40), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name=op.f("fk_applicability_decisions_company_id_companies"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_applicability_decisions")),
    )
    with op.batch_alter_table("applicability_decisions", schema=None) as batch_op:
        batch_op.create_index("ix_applicability_company_set", ["company_id", "set_key"], unique=False)
        batch_op.create_index(batch_op.f("ix_applicability_decisions_org_id"), ["org_id"], unique=False)

    op.create_table(
        "assessment_runs",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("org_id", sa.String(length=40), nullable=False),
        sa.Column("company_id", sa.String(length=40), nullable=False),
        sa.Column("requirement_set_id", sa.String(length=120), nullable=False),
        sa.Column("mode", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("label", sa.String(length=200), nullable=True),
        sa.Column("period_label", sa.String(length=40), nullable=True),
        sa.Column("period_start", sa.Date(), nullable=True),
        sa.Column("period_end", sa.Date(), nullable=True),
        sa.Column("deadline", sa.Date(), nullable=True),
        sa.Column("pipeline_version", sa.String(length=40), nullable=True),
        sa.Column("extraction_version", sa.String(length=40), nullable=True),
        sa.Column("rules_version", sa.String(length=40), nullable=True),
        sa.Column("prompt_version", sa.String(length=40), nullable=True),
        sa.Column("llm_provider", sa.String(length=80), nullable=True),
        sa.Column("llm_model", sa.String(length=120), nullable=True),
        sa.Column(
            "llm_config",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column(
            "input_manifest",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column(
            "excluded_requirements",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column(
            "metrics",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column(
            "summary",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("previous_run_id", sa.String(length=40), nullable=True),
        sa.Column("job_id", sa.String(length=40), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(length=40), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name=op.f("fk_assessment_runs_company_id_companies"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["org_id"],
            ["organizations.id"],
            name=op.f("fk_assessment_runs_org_id_organizations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["requirement_set_id"],
            ["requirement_sets.id"],
            name=op.f("fk_assessment_runs_requirement_set_id_requirement_sets"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_assessment_runs")),
    )
    with op.batch_alter_table("assessment_runs", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_assessment_runs_org_id"), ["org_id"], unique=False)
        batch_op.create_index("ix_runs_company_created", ["company_id", "created_at"], unique=False)

    op.create_table(
        "company_peers",
        sa.Column("company_id", sa.String(length=40), nullable=False),
        sa.Column("peer_id", sa.String(length=40), nullable=False),
        sa.Column("org_id", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name=op.f("fk_company_peers_company_id_companies"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["peer_id"], ["companies.id"], name=op.f("fk_company_peers_peer_id_companies"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("company_id", "peer_id", name=op.f("pk_company_peers")),
    )
    with op.batch_alter_table("company_peers", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_company_peers_org_id"), ["org_id"], unique=False)

    op.create_table(
        "documents",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("org_id", sa.String(length=40), nullable=False),
        sa.Column("company_id", sa.String(length=40), nullable=False),
        sa.Column("lineage_id", sa.String(length=40), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("doc_type", sa.String(length=40), nullable=False),
        sa.Column("filename", sa.String(length=300), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("storage_key", sa.String(length=500), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column(
            "page_sizes",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("period_label", sa.String(length=40), nullable=True),
        sa.Column("period_start", sa.Date(), nullable=True),
        sa.Column("period_end", sa.Date(), nullable=True),
        sa.Column("published_on", sa.Date(), nullable=True),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "ocr_pages",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column(
            "processing_stats",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("pipeline_version", sa.String(length=40), nullable=True),
        sa.Column("extraction_version", sa.String(length=40), nullable=True),
        sa.Column("is_sample", sa.Boolean(), nullable=False),
        sa.Column("uploaded_by", sa.String(length=40), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("superseded_by", sa.String(length=40), nullable=True),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name=op.f("fk_documents_company_id_companies"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["org_id"],
            ["organizations.id"],
            name=op.f("fk_documents_org_id_organizations"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_documents")),
    )
    with op.batch_alter_table("documents", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_documents_company_id"), ["company_id"], unique=False)
        batch_op.create_index("ix_documents_company_lineage", ["company_id", "lineage_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_documents_org_id"), ["org_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_documents_sha256"), ["sha256"], unique=False)

    op.create_table(
        "findings",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("org_id", sa.String(length=40), nullable=False),
        sa.Column("run_id", sa.String(length=40), nullable=False),
        sa.Column("company_id", sa.String(length=40), nullable=False),
        sa.Column("requirement_id", sa.String(length=160), nullable=False),
        sa.Column("requirement_code", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("completeness", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("rules_rationale", sa.Text(), nullable=False),
        sa.Column(
            "element_results",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column(
            "missing_elements",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("requires_human_review", sa.Boolean(), nullable=False),
        sa.Column(
            "review_reasons",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("method", sa.String(length=20), nullable=False),
        sa.Column("rules_status", sa.String(length=30), nullable=True),
        sa.Column("llm_status", sa.String(length=30), nullable=True),
        sa.Column(
            "llm_output",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=True,
        ),
        sa.Column(
            "citation_check",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column(
            "conflicts",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column(
            "priority",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column(
            "retrieval",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["requirement_id"], ["requirements.id"], name=op.f("fk_findings_requirement_id_requirements")
        ),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["assessment_runs.id"],
            name=op.f("fk_findings_run_id_assessment_runs"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_findings")),
        sa.UniqueConstraint("run_id", "requirement_id", name=op.f("uq_findings_run_id")),
    )
    with op.batch_alter_table("findings", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_findings_company_id"), ["company_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_findings_org_id"), ["org_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_findings_run_id"), ["run_id"], unique=False)

    op.create_table(
        "passages",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("org_id", sa.String(length=40), nullable=False),
        sa.Column("company_id", sa.String(length=40), nullable=False),
        sa.Column("document_id", sa.String(length=40), nullable=False),
        sa.Column("page", sa.Integer(), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("section", sa.String(length=300), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column(
            "bbox",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("extraction_method", sa.String(length=20), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("table_ref", sa.String(length=60), nullable=True),
        sa.Column(
            "cells",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            name=op.f("fk_passages_document_id_documents"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_passages")),
    )
    with op.batch_alter_table("passages", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_passages_company_id"), ["company_id"], unique=False)
        batch_op.create_index("ix_passages_document_page", ["document_id", "page"], unique=False)
        batch_op.create_index(batch_op.f("ix_passages_org_id"), ["org_id"], unique=False)

    op.create_table(
        "extracted_metrics",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("org_id", sa.String(length=40), nullable=False),
        sa.Column("company_id", sa.String(length=40), nullable=False),
        sa.Column("document_id", sa.String(length=40), nullable=False),
        sa.Column("passage_id", sa.String(length=40), nullable=False),
        sa.Column("metric_key", sa.String(length=60), nullable=False),
        sa.Column("label", sa.String(length=300), nullable=True),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=40), nullable=True),
        sa.Column("normalized_value", sa.Float(), nullable=True),
        sa.Column("normalized_unit", sa.String(length=40), nullable=True),
        sa.Column("period_label", sa.String(length=40), nullable=True),
        sa.Column("period_start", sa.Date(), nullable=True),
        sa.Column("period_end", sa.Date(), nullable=True),
        sa.Column(
            "qualifiers",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("method", sa.String(length=20), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            name=op.f("fk_extracted_metrics_document_id_documents"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["passage_id"],
            ["passages.id"],
            name=op.f("fk_extracted_metrics_passage_id_passages"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_extracted_metrics")),
    )
    with op.batch_alter_table("extracted_metrics", schema=None) as batch_op:
        batch_op.create_index("ix_extracted_metrics_company_key", ["company_id", "metric_key"], unique=False)
        batch_op.create_index(batch_op.f("ix_extracted_metrics_document_id"), ["document_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_extracted_metrics_org_id"), ["org_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_extracted_metrics_passage_id"), ["passage_id"], unique=False)

    op.create_table(
        "finding_evidence",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("finding_id", sa.String(length=40), nullable=False),
        sa.Column("passage_id", sa.String(length=40), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column(
            "element_keys",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("metric_id", sa.String(length=40), nullable=True),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["finding_id"],
            ["findings.id"],
            name=op.f("fk_finding_evidence_finding_id_findings"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["passage_id"], ["passages.id"], name=op.f("fk_finding_evidence_passage_id_passages")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_finding_evidence")),
    )
    with op.batch_alter_table("finding_evidence", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_finding_evidence_finding_id"), ["finding_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_finding_evidence_passage_id"), ["passage_id"], unique=False)

    op.create_table(
        "reviews",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("org_id", sa.String(length=40), nullable=False),
        sa.Column("finding_id", sa.String(length=40), nullable=False),
        sa.Column("reviewer_id", sa.String(length=40), nullable=True),
        sa.Column("reviewer_name", sa.String(length=200), nullable=True),
        sa.Column("decision", sa.String(length=20), nullable=False),
        sa.Column("previous_status", sa.String(length=30), nullable=False),
        sa.Column("new_status", sa.String(length=30), nullable=True),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["finding_id"], ["findings.id"], name=op.f("fk_reviews_finding_id_findings"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reviews")),
    )
    with op.batch_alter_table("reviews", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_reviews_finding_id"), ["finding_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_reviews_org_id"), ["org_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("reviews", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_reviews_org_id"))
        batch_op.drop_index(batch_op.f("ix_reviews_finding_id"))

    op.drop_table("reviews")
    with op.batch_alter_table("finding_evidence", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_finding_evidence_passage_id"))
        batch_op.drop_index(batch_op.f("ix_finding_evidence_finding_id"))

    op.drop_table("finding_evidence")
    with op.batch_alter_table("extracted_metrics", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_extracted_metrics_passage_id"))
        batch_op.drop_index(batch_op.f("ix_extracted_metrics_org_id"))
        batch_op.drop_index(batch_op.f("ix_extracted_metrics_document_id"))
        batch_op.drop_index("ix_extracted_metrics_company_key")

    op.drop_table("extracted_metrics")
    with op.batch_alter_table("passages", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_passages_org_id"))
        batch_op.drop_index("ix_passages_document_page")
        batch_op.drop_index(batch_op.f("ix_passages_company_id"))

    op.drop_table("passages")
    with op.batch_alter_table("findings", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_findings_run_id"))
        batch_op.drop_index(batch_op.f("ix_findings_org_id"))
        batch_op.drop_index(batch_op.f("ix_findings_company_id"))

    op.drop_table("findings")
    with op.batch_alter_table("documents", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_documents_sha256"))
        batch_op.drop_index(batch_op.f("ix_documents_org_id"))
        batch_op.drop_index("ix_documents_company_lineage")
        batch_op.drop_index(batch_op.f("ix_documents_company_id"))

    op.drop_table("documents")
    with op.batch_alter_table("company_peers", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_company_peers_org_id"))

    op.drop_table("company_peers")
    with op.batch_alter_table("assessment_runs", schema=None) as batch_op:
        batch_op.drop_index("ix_runs_company_created")
        batch_op.drop_index(batch_op.f("ix_assessment_runs_org_id"))

    op.drop_table("assessment_runs")
    with op.batch_alter_table("applicability_decisions", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_applicability_decisions_org_id"))
        batch_op.drop_index("ix_applicability_company_set")

    op.drop_table("applicability_decisions")
    with op.batch_alter_table("actions", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_actions_org_id"))
        batch_op.drop_index("ix_actions_company_gap")

    op.drop_table("actions")
    with op.batch_alter_table("usage_events", schema=None) as batch_op:
        batch_op.drop_index("ix_usage_events_org_kind_created")

    op.drop_table("usage_events")
    with op.batch_alter_table("requirements", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_requirements_set_id"))

    op.drop_table("requirements")
    with op.batch_alter_table("memberships", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_memberships_user_id"))
        batch_op.drop_index(batch_op.f("ix_memberships_org_id"))

    op.drop_table("memberships")
    with op.batch_alter_table("companies", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_companies_org_id"))

    op.drop_table("companies")
    op.drop_table("users")
    with op.batch_alter_table("requirement_sets", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_requirement_sets_key"))

    op.drop_table("requirement_sets")
    op.drop_table("organizations")
    op.drop_table("llm_cache")
    with op.batch_alter_table("jobs", schema=None) as batch_op:
        batch_op.drop_index("ix_jobs_status_run_after")
        batch_op.drop_index(batch_op.f("ix_jobs_org_id"))

    op.drop_table("jobs")
    with op.batch_alter_table("enquiries", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_enquiries_kind"))

    op.drop_table("enquiries")
    with op.batch_alter_table("audit_events", schema=None) as batch_op:
        batch_op.drop_index("ix_audit_events_org_created")

    op.drop_table("audit_events")
