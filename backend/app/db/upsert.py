from sqlalchemy import Table
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.orm import Session


def insert_ignore(
    db: Session,
    table: Table,
    constraint: str,
    **values,
):
    """Build an INSERT that silently skips rows already present.

    Emits the dialect-appropriate "upsert that never updates":

    * PostgreSQL: ``INSERT ... ON CONFLICT ON CONSTRAINT <name> DO NOTHING``
    * SQLite:     ``INSERT ... ON CONFLICT DO NOTHING`` (target-less form,
      which matches any unique/primary key violation)

    Prefer this over ``sqlalchemy.dialects.postgresql.insert`` directly so the
    same code runs against the SQLite test database.
    """
    dialect = db.get_bind().dialect.name

    if dialect == "postgresql":
        return (
            postgresql.insert(table)
            .values(**values)
            .on_conflict_do_nothing(constraint=constraint)
        )

    if dialect == "sqlite":
        return (
            sqlite.insert(table)
            .values(**values)
            .on_conflict_do_nothing()
        )

    raise NotImplementedError(
        f"insert_ignore is not implemented for dialect {dialect!r}"
    )