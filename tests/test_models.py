import tempfile
import unittest
from pathlib import Path

from sqlalchemy.pool import QueuePool, StaticPool

from simple_image.models import (
    _is_sqlite_memory_url,
    _is_sqlite_url,
    _normalize_database_url,
    create_session_factory,
)


class DatabaseConfigurationTests(unittest.TestCase):
    def test_file_sqlite_uses_wal_and_connection_pragmas(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            session_factory = create_session_factory(
                default_compress_quality=25,
                db_path=Path(temp_dir) / "database.db",
            )
            engine = session_factory.kw["bind"]

            self.assertIsInstance(engine.pool, QueuePool)
            with engine.connect() as first, engine.connect() as second:
                self.assertIsNot(
                    first.connection.dbapi_connection,
                    second.connection.dbapi_connection,
                )
                for connection in (first, second):
                    self.assertEqual(
                        connection.exec_driver_sql("PRAGMA journal_mode").scalar_one(),
                        "wal",
                    )
                    self.assertEqual(
                        connection.exec_driver_sql("PRAGMA synchronous").scalar_one(),
                        1,
                    )
                    self.assertEqual(
                        connection.exec_driver_sql("PRAGMA busy_timeout").scalar_one(),
                        30000,
                    )
                    self.assertEqual(
                        connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one(),
                        1,
                    )
                    self.assertEqual(
                        connection.exec_driver_sql("PRAGMA wal_autocheckpoint").scalar_one(),
                        1000,
                    )
                    self.assertEqual(
                        connection.exec_driver_sql("PRAGMA journal_size_limit").scalar_one(),
                        67108864,
                    )
            engine.dispose()

    def test_sqlite_driver_url_is_detected(self):
        self.assertTrue(_is_sqlite_url("sqlite+pysqlite:///database.db"))
        self.assertFalse(_is_sqlite_memory_url("sqlite+pysqlite:///database.db"))

    def test_memory_sqlite_uses_static_pool_without_wal(self):
        session_factory = create_session_factory(
            default_compress_quality=25,
            database_url="sqlite+pysqlite:///:memory:",
        )
        engine = session_factory.kw["bind"]

        self.assertIsInstance(engine.pool, StaticPool)
        with engine.connect() as connection:
            self.assertEqual(
                connection.exec_driver_sql("PRAGMA journal_mode").scalar_one(),
                "memory",
            )
            self.assertEqual(
                connection.exec_driver_sql("PRAGMA busy_timeout").scalar_one(),
                30000,
            )
            self.assertEqual(
                connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one(),
                1,
            )
        engine.dispose()

    def test_mysql_url_normalization_remains_non_sqlite(self):
        normalized = _normalize_database_url("mysql://user:password@localhost/db")

        self.assertEqual(normalized, "mysql+pymysql://user:password@localhost/db")
        self.assertFalse(_is_sqlite_url(normalized))


if __name__ == "__main__":
    unittest.main()
