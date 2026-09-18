import argparse
import os
import sys
from pathlib import Path

import uvicorn

from .main import create_app


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
        "-d", "--daemon", action="store_true",
        help="Run server as a background daemon",
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
    )
    uvicorn.run(app, host=args.host, port=args.port, reload=args.reload)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "serve":
        run_serve(args)


if __name__ == "__main__":
    main()
