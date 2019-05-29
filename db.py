import mysql.connector
from typing import Union, Dict, List, Optional, Tuple, Any

import config


class DbConnection:
    def __init__(self):
        self.conn = None  # type: Optional[mysql.connector.MySQLConnection]

    def __enter__(self):
        args = {
            "user": config.DB_USER,
            "password": config.DB_PASS,
            "database": config.DB_NAME,
            "charset": "utf8mb4",
            "collation": "utf8mb4_unicode_ci"
        }

        if config.DB_HOST[0] == "/":
            # using unix socket
            args["unix_socket"] = config.DB_HOST
        else:
            args["host"] = config.DB_HOST
            args["port"] = config.DB_PORT

        self.conn = mysql.connector.connect(**args)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close the db connection and commit/rollback any pending transactions.

        If an exception was raised, we rollback. Otherwise, we commit.
        """
        if self.conn and self.conn.is_connected():
            try:
                if exc_type is None:
                    self.conn.commit()
                else:
                    self.conn.rollback()
            finally:
                self.conn.close()
                self.conn = None  # type: Optional[mysql.connector.MySQLConnection]

    def execute(self, operation: Any, params: Tuple = (), multi: bool = False)\
            -> Union[int, List[Union[int, Dict[str, Any], List[Dict[str, Any]]]]]:
        c = self.conn.cursor(dictionary=True)
        try:
            result = c.execute(operation, params=params, multi=multi)
            if multi:
                data = []
                for r in result:
                    if r.with_rows:
                        data.append(r.fetchall())
                    else:
                        data.append(r.rowcount)
            else:
                if c.with_rows:
                    data = c.fetchall()
                else:
                    data = c.rowcount
        finally:
            c.close()
        return data

    def fetch(self, operation: Any, params: Tuple = ()) -> Optional[Dict[str, Any]]:
        """
        Fetches the first row of the result set, or None if there are no results.

        Returns None if the operation is not a SELECT query as well. Use execute if you
        wish to retrieve the number of affected rows for a DML query.

        :param operation: SQL query
        :param params: Parameters for the query
        :return: The first row or None
        """
        data = self.execute(operation, params)
        if isinstance(data, list):
            try:
                return data[0]
            except IndexError:
                return None  # no results
        return None  # not a query that returned data, so return None
