import db


def run():
    """Run cron tasks (deleting expired stuff)"""
    with db.DbConnection() as conn:
        conn.execute("DELETE FROM pastes WHERE paste_expires IS NOT NULL AND paste_expires < UTC_TIMESTAMP()")


if __name__ == "__main__":
    run()
