"""Add admin_audit_log table

Logs who did what, when, for admin actions that change state - not a
generic audit-everything framework, just the specific admin-write
endpoints that already exist (make/revoke-admin, comp/revoke a
subscription, hide/unhide content, secret writes, pricing changes).

Revision ID: 020
Revises: 019
Create Date: 2026-11-10

"""

from alembic import op

revision = "020"
down_revision = "019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS admin_audit_log (
            id SERIAL PRIMARY KEY,
            admin_user_id INTEGER NOT NULL,
            admin_email VARCHAR(255) NOT NULL,
            action VARCHAR(100) NOT NULL,
            target_type VARCHAR(50),
            target_id VARCHAR(100),
            detail TEXT DEFAULT '',
            created_at TIMESTAMPTZ DEFAULT now()
        )
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_admin_audit_log_admin_user_id "
        "ON admin_audit_log (admin_user_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_admin_audit_log_action "
        "ON admin_audit_log (action)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_admin_audit_log_created_at "
        "ON admin_audit_log (created_at)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_admin_audit_log_created_at")
    op.execute("DROP INDEX IF EXISTS ix_admin_audit_log_action")
    op.execute("DROP INDEX IF EXISTS ix_admin_audit_log_admin_user_id")
    op.execute("DROP TABLE IF EXISTS admin_audit_log")
