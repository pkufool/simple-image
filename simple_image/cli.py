import argparse
import getpass
import os
import sys
from pathlib import Path

import uvicorn
from sqlalchemy.engine import make_url

from .main import create_app, hash_password, verify_password
from .models import (
    DEFAULT_COMPRESS_QUALITY,
    SessionToken,
    User,
    create_session_factory,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="simple-image", description="Simple Image server CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    serve = subparsers.add_parser("serve", help="Run HTTP server")
    serve.add_argument("data_dir", type=Path, help="Runtime data directory (DB + images)")
    serve.add_argument("--host", default="0.0.0.0", help="Bind host")
    serve.add_argument("--port", type=int, default=8000, help="Bind port")
    serve.add_argument("--reload", action="store_true", help="Enable auto reload")
    serve.add_argument("--api-url", default=None, help="Public API base URL")
    serve.add_argument("--admin-username", default=None, help="Bootstrap admin username")
    serve.add_argument("--admin-password", default=None, help="Bootstrap admin password")
    serve.add_argument(
        "--database-url",
        default=None,
        help="Database URL, e.g. mysql+pymysql://user:pass@host:3306/simple_image",
    )
    serve.add_argument(
        "--compress-quality",
        type=int,
        default=None,
        help="Default upload compress quality (1-95)",
    )
    serve.add_argument(
        "--base-path",
        default=None,
        help="Deploy under sub path, e.g. /simple_image",
    )
    serve.add_argument(
        "--allowed-image-domain",
        action="append",
        default=None,
        help="Allow image access from this domain; repeat as needed (supports *.example.com)",
    )
    serve.add_argument(
        "-d", "--daemon", action="store_true",
        help="Run server as a background daemon",
    )

    reset_pwd = subparsers.add_parser(
        "reset-admin-password", help="Reset admin password"
    )
    reset_pwd.add_argument(
        "data_dir", type=Path, help="Runtime data directory (same as used by serve)"
    )
    reset_pwd.add_argument(
        "--username", default=None,
        help="Admin username to reset (omit to auto-select the only admin)"
    )
    reset_pwd.add_argument(
        "--database-url", default=None,
        help="Database URL (omit to use data_dir/database.db)"
    )

    return parser


def _daemonize(data_dir: Path) -> None:
    """Double-fork to detach from the controlling terminal."""
    data_dir.mkdir(parents=True, exist_ok=True)
    pid_file = data_dir / "simple-image.pid"
    log_file = data_dir / "simple-image.log"

    # First fork – exit parent
    if os.fork() > 0:
        raise SystemExit(0)

    os.setsid()

    # Second fork – prevent re-acquiring a terminal
    if os.fork() > 0:
        raise SystemExit(0)

    # Redirect stdio to log file
    log_fd = os.open(str(log_file), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    os.dup2(log_fd, sys.stdout.fileno())
    os.dup2(log_fd, sys.stderr.fileno())
    os.close(log_fd)

    # Write PID file
    pid_file.write_text(str(os.getpid()))


def run_serve(args: argparse.Namespace) -> None:
    if args.daemon:
        _daemonize(args.data_dir)

    app = create_app(
        data_dir=args.data_dir,
        api_url=args.api_url,
        admin_username=args.admin_username,
        admin_password=args.admin_password,
        default_compress_quality=args.compress_quality,
        database_url=args.database_url,
        base_path=args.base_path,
        allowed_image_domains=args.allowed_image_domain,
    )
    uvicorn.run(app, host=args.host, port=args.port, reload=args.reload)


def run_reset_admin_password(args: argparse.Namespace) -> None:
    db_path = (args.data_dir / "database.db").expanduser().resolve()
    database_url = (
        args.database_url
        or os.getenv("SIMPLE_IMAGE_DATABASE_URL")
        or os.getenv("DATABASE_URL")
    )
    if not database_url:
        if not db_path.exists():
            print(f"Error: database not found at {db_path}", file=sys.stderr)
            raise SystemExit(1)
        database_url = f"sqlite:///{db_path}"
        print(f"Using SQLite database: {db_path}")
    else:
        parsed_url = make_url(database_url)
        if parsed_url.get_backend_name() == "sqlite" and parsed_url.database not in (
            None,
            "",
            ":memory:",
        ):
            configured_path = Path(parsed_url.database).expanduser()
            if not configured_path.is_absolute():
                configured_path = (Path.cwd() / configured_path).resolve()
            print(f"Using SQLite database: {configured_path}")
        else:
            print(f"Using configured database: {parsed_url.render_as_string(hide_password=True)}")

    session_factory = create_session_factory(
        default_compress_quality=DEFAULT_COMPRESS_QUALITY,
        database_url=database_url,
    )
    engine = session_factory.kw["bind"]
    target_username = None
    new_password = None
    db = session_factory()
    try:
        admins = db.query(User).filter(User.is_admin.is_(True)).all()

        if not admins:
            print("Error: no admin user found in the database.", file=sys.stderr)
            raise SystemExit(1)

        if args.username:
            target = next((u for u in admins if u.username == args.username), None)
            if not target:
                available = ", ".join(u.username for u in admins)
                print(
                    f"Error: admin '{args.username}' not found. Existing admins: {available}",
                    file=sys.stderr,
                )
                raise SystemExit(1)
        elif len(admins) == 1:
            target = admins[0]
            print(f"Found admin user: {target.username}")
        else:
            print("Multiple admin users found, please specify --username:")
            for user in admins:
                print(f"  - {user.username}")
            raise SystemExit(1)

        new_password = getpass.getpass(f"New password for '{target.username}': ")
        if not new_password:
            print("Error: password cannot be empty.", file=sys.stderr)
            raise SystemExit(1)
        confirm = getpass.getpass("Confirm new password: ")
        if new_password != confirm:
            print("Error: passwords do not match.", file=sys.stderr)
            raise SystemExit(1)

        target_username = target.username
        target.password_hash = hash_password(new_password)
        db.query(SessionToken).filter(SessionToken.user_id == target.id).delete()
        db.commit()
    finally:
        db.close()
        engine.dispose()

    verify_factory = create_session_factory(
        default_compress_quality=DEFAULT_COMPRESS_QUALITY,
        database_url=database_url,
    )
    verify_engine = verify_factory.kw["bind"]
    verify_db = verify_factory()
    try:
        saved_admin = (
            verify_db.query(User)
            .filter(User.username == target_username, User.is_admin.is_(True))
            .one_or_none()
        )
        if not saved_admin or not verify_password(new_password, saved_admin.password_hash):
            print("Error: password reset could not be verified.", file=sys.stderr)
            raise SystemExit(1)
    finally:
        verify_db.close()
        verify_engine.dispose()

    print(
        f"Password for admin '{target_username}' has been reset successfully; "
        "existing sessions were signed out."
    )


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "serve":
        run_serve(args)
    elif args.command == "reset-admin-password":
        run_reset_admin_password(args)


if __name__ == "__main__":
    main()
