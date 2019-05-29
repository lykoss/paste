from typing import Set
import pathlib
from db import DbConnection


def run():
    """
    Execute the installer.

    The installer will get the database schema up to current as well as set up any necessary
    ancillary structures such as ElasticSearch indices and pipelines.

    :return:
    """
    with DbConnection() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS migrations (
            migration_key varchar(150) PRIMARY KEY,
            migration_time datetime) ENGINE=InnoDB CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci""")
        applied_migrations = set()
        for row in conn.execute("SELECT migration_key FROM migrations"):
            applied_migrations.add(row["migration_key"])
        for p in sorted(pathlib.Path("migrations").iterdir()):
            filename = str(p.name)
            filepath = str(p.absolute())
            if p.is_file() and filename[-4:] == ".sql":
                _apply_migration(filename[:-4], filepath, conn, applied_migrations)


def _apply_migration(name: str, path: str, conn: DbConnection, already_applied: Set[str]) -> None:
    """
    Check if a migration is applied and if not, run it.

    :param name: Migration name (key). This must be unique.
    :param path: Path to migration sql file.
    :param conn: Already-open database connection.
    :param already_applied: A set of which migrations have already been applied. The current migration will be
        added to this set if successful.
    :return:
    """
    if name in already_applied:
        return

    with open(path, "r") as f:
        conn.execute(f.read(), multi=True)
        already_applied.add(name)
        conn.execute("INSERT INTO migrations (migration_key, migration_time) VALUES (%s, NOW())",
                     (name,))


if __name__ == "__main__":
    run()
