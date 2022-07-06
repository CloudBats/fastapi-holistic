"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""

from alembic import op
import sqlalchemy as sa

from fastapi_laser.alembic_ext.steps import MigrationStep
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}

${"\n".join(enum_args_variable_assignments) if enum_args_variable_assignments else "# no generated enum definitions"}
migration_steps = [
    ${",\n    ".join(migration_steps) if migration_steps else "# no generated migration steps"}
]


def upgrade():
    for step in migration_steps:
        step.pre_upgrade()

    ${upgrades if upgrades else "# no generated upgrades"}

    for step in migration_steps:
        step.post_upgrade()


def downgrade():
    for step in migration_steps:
        step.pre_downgrade()

    ${downgrades if downgrades else "# no generated downgrades"}

    for step in migration_steps:
        step.post_downgrade()
