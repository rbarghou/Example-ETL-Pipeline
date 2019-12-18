"""task 1 create tables

Revision ID: 64f0cb642938
Revises: 
Create Date: 2019-12-06 22:01:49.824374

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "64f0cb642938"
down_revision = None
branch_labels = None
depends_on = None


"""
Typically at this point I would like to convert the raw sql to the code native
 to the ORM I'm using, but in this case I would rather keep as much fidelity as
 possible to the original design as possible without making some silly mistake.

Of course this would depend on the complexity of the sql file I was given.

If the sqlfile was an extremely complicated one, then my approach would depend
 on the organizational needs, risks, etc.
"""

with open("./versions/task_1_create_tables.sql") as f:
    raw_sql = f.read()


def upgrade():
    for cmd in raw_sql.split(";"):
        op.execute(cmd.strip())


def downgrade():
    op.execute("SET FOREIGN_KEY_CHECKS=0")
    for table in ["samples", "sample_measurements"]:
        op.drop_table(table)
    op.execute("SET FOREIGN_KEY_CHECKS=1")
