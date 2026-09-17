import argparse
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

    return parser


def run_serve(args: argparse.Namespace) -> None:
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
