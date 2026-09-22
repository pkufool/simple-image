import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from simple_image.cli import run_reset_admin_password
from simple_image.main import create_app, verify_password
from simple_image.models import SessionToken, User


def request_app(app, method, path, body=None, headers=()):
    import asyncio

    status_code = None
    response_headers = []
    response_body = bytearray()
    payload = body or b""

    async def receive():
        return {"type": "http.request", "body": payload, "more_body": False}

    async def send(message):
        nonlocal status_code, response_headers
        if message["type"] == "http.response.start":
            status_code = message["status"]
            response_headers = message["headers"]
        elif message["type"] == "http.response.body":
            response_body.extend(message.get("body", b""))

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("ascii"),
        "query_string": b"",
        "root_path": "",
        "headers": [
            (name.lower().encode("ascii"), value.encode("utf-8"))
            for name, value in headers
        ],
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
    }
    asyncio.run(app(scope, receive, send))
    return status_code, dict(response_headers), bytes(response_body)


class AdminPasswordTests(unittest.TestCase):
    def test_import_does_not_create_database(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir) / "runtime"
            env = os.environ.copy()
            env["SIMPLE_IMAGE_DATA_DIR"] = str(data_dir)
            subprocess.run(
                [sys.executable, "-c", "import simple_image; import simple_image.main"],
                check=True,
                cwd=Path(__file__).parents[1],
                env=env,
            )
            self.assertFalse(data_dir.exists())

    def test_reset_works_while_service_engine_stays_open(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)
            app = create_app(data_dir=data_dir)
            service_engine = app.state.session_local.kw["bind"]
            login_status, login_headers, _ = request_app(
                app,
                "POST",
                "/auth/login",
                json.dumps(
                    {"username": "admin", "password": "admin123456"}
                ).encode("utf-8"),
                [("Content-Type", "application/json")],
            )
            self.assertEqual(login_status, 200)
            session_cookie = login_headers[b"set-cookie"].decode("utf-8").split(";", 1)[0]

            args = SimpleNamespace(
                data_dir=data_dir,
                database_url=None,
                username="admin",
            )
            output = io.StringIO()
            with patch(
                "simple_image.cli.getpass.getpass",
                side_effect=["new-admin-password", "new-admin-password"],
            ), redirect_stdout(output):
                run_reset_admin_password(args)

            self.assertIn(str((data_dir / "database.db").resolve()), output.getvalue())
            old_status, _, _ = request_app(
                app,
                "POST",
                "/auth/login",
                json.dumps(
                    {"username": "admin", "password": "admin123456"}
                ).encode("utf-8"),
                [("Content-Type", "application/json")],
            )
            self.assertEqual(old_status, 401)

            new_status, new_headers, _ = request_app(
                app,
                "POST",
                "/auth/login",
                json.dumps(
                    {"username": "admin", "password": "new-admin-password"}
                ).encode("utf-8"),
                [("Content-Type", "application/json")],
            )
            self.assertEqual(new_status, 200)
            new_cookie = new_headers[b"set-cookie"].decode("utf-8").split(";", 1)[0]

            create_status, _, _ = request_app(
                app,
                "POST",
                "/admin/users",
                json.dumps(
                    {"username": "new-user", "password": "user-password"}
                ).encode("utf-8"),
                [("Content-Type", "application/json"), ("Cookie", new_cookie)],
            )
            self.assertEqual(create_status, 200)

            stale_status, _, _ = request_app(
                app,
                "GET",
                "/auth/me",
                headers=[("Cookie", session_cookie)],
            )
            self.assertEqual(stale_status, 401)

            db = app.state.session_local()
            try:
                admin = db.query(User).filter(User.username == "admin").one()
                self.assertTrue(
                    verify_password("new-admin-password", admin.password_hash)
                )
                self.assertFalse(verify_password("admin123456", admin.password_hash))
                self.assertEqual(
                    db.query(SessionToken)
                    .filter(SessionToken.user_id == admin.id)
                    .count(),
                    1,
                )
            finally:
                db.close()
                service_engine.dispose()


if __name__ == "__main__":
    unittest.main()
