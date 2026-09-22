import asyncio
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI, HTTPException
from starlette.requests import Request

from simple_image.cli import build_parser
from simple_image.main import (
    create_app,
    enforce_image_domain,
    image_disk_path,
    image_domain_matches,
    image_response_headers,
    normalize_allowed_image_domains,
)


def make_request(app, headers=()):
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/image/example",
            "headers": [
                (name.lower().encode("ascii"), value.encode("utf-8"))
                for name, value in headers
            ],
            "app": app,
        }
    )


def request_app(app, path, headers=()):
    status_code = None
    response_headers = []
    response_body = bytearray()

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

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
        "method": "GET",
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


class ImageDomainConfigurationTests(unittest.TestCase):
    def test_normalizes_exact_wildcard_and_idna_domains(self):
        domains = normalize_allowed_image_domains(
            ["Example.COM.", "*.Example.com", "例子.测试", "example.com"]
        )

        self.assertEqual(
            domains,
            ("example.com", "*.example.com", "xn--fsqu00a.xn--0zwm56d"),
        )

    def test_exact_and_wildcard_matching(self):
        self.assertTrue(image_domain_matches("example.com", ("example.com",)))
        self.assertFalse(image_domain_matches("www.example.com", ("example.com",)))
        self.assertTrue(image_domain_matches("www.example.com", ("*.example.com",)))
        self.assertTrue(image_domain_matches("a.b.example.com", ("*.example.com",)))
        self.assertFalse(image_domain_matches("example.com", ("*.example.com",)))
        self.assertFalse(image_domain_matches("evilexample.com", ("*.example.com",)))

    def test_rejects_invalid_domain_rules(self):
        invalid_rules = (
            "https://example.com",
            "example.com/path",
            "example.com:443",
            "foo.*.example.com",
            "*example.com",
            "-example.com",
            "example..com",
        )
        for rule in invalid_rules:
            with self.subTest(rule=rule):
                with self.assertRaises(ValueError):
                    normalize_allowed_image_domains([rule])

    def test_create_app_uses_environment_and_explicit_empty_override(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(
                os.environ,
                {"SIMPLE_IMAGE_ALLOWED_DOMAINS": "example.com,*.trusted.test"},
            ):
                configured = create_app(data_dir=Path(temp_dir) / "configured")
                unrestricted = create_app(
                    data_dir=Path(temp_dir) / "unrestricted",
                    allowed_image_domains=[],
                )
                configured_engine = configured.state.session_local.kw["bind"]
                unrestricted_engine = unrestricted.state.session_local.kw["bind"]

            self.assertEqual(
                configured.state.allowed_image_domains,
                ("example.com", "*.trusted.test"),
            )
            self.assertEqual(unrestricted.state.allowed_image_domains, ())
            configured_engine.dispose()
            unrestricted_engine.dispose()

    def test_index_injects_public_media_url(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            app = create_app(
                data_dir=temp_dir,
                api_url="https://r.kingway.space/",
            )
            try:
                status_code, _, body = request_app(app, "/")
                rendered = body.decode("utf-8")
                self.assertEqual(status_code, 200)
                self.assertIn(
                    'name="simple-image-public-url" content="https://r.kingway.space"',
                    rendered,
                )
                self.assertNotIn("__SIMPLE_IMAGE_PUBLIC_URL__", rendered)
            finally:
                app.state.session_local.kw["bind"].dispose()

    def test_cli_accepts_repeated_domains(self):
        args = build_parser().parse_args(
            [
                "serve",
                "data",
                "--allowed-image-domain",
                "example.com",
                "--allowed-image-domain",
                "*.trusted.test",
            ]
        )

        self.assertEqual(
            args.allowed_image_domain,
            ["example.com", "*.trusted.test"],
        )


class ImageDomainEnforcementTests(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.state.allowed_image_domains = ("example.com", "*.trusted.test")

    def assert_forbidden(self, headers=()):
        with self.assertRaises(HTTPException) as raised:
            enforce_image_domain(make_request(self.app, headers))
        self.assertEqual(raised.exception.status_code, 403)
        self.assertEqual(raised.exception.headers["Cache-Control"], "private, no-store")
        self.assertEqual(raised.exception.headers["Vary"], "Origin, Referer")

    def test_unconfigured_mode_allows_missing_source(self):
        self.app.state.allowed_image_domains = ()

        enforce_image_domain(make_request(self.app))
        self.assertEqual(
            image_response_headers(self.app),
            {"Cache-Control": "public, max-age=2592000"},
        )

    def test_allows_matching_origin_or_referer(self):
        enforce_image_domain(
            make_request(self.app, [("Origin", "https://example.com")])
        )
        enforce_image_domain(
            make_request(
                self.app,
                [("Referer", "https://a.trusted.test/gallery?id=1")],
            )
        )

    def test_origin_takes_precedence_over_allowed_referer(self):
        self.assert_forbidden(
            [
                ("Origin", "https://blocked.test"),
                ("Referer", "https://example.com/gallery"),
            ]
        )

    def test_strict_mode_rejects_missing_or_invalid_source(self):
        cases = (
            (),
            (("Origin", "null"),),
            (("Origin", "file://example.com"),),
            (("Origin", "https://user@example.com"),),
            (("Origin", "https://example.com/path"),),
            (("Referer", "not-a-url"),),
            (("Referer", "https://blocked.test/page"),),
            (("Origin", "https://example.com, https://blocked.test"),),
            (("Origin", "https://example.com"), ("Origin", "https://example.com")),
        )
        for headers in cases:
            with self.subTest(headers=headers):
                self.assert_forbidden(headers)

    def test_restricted_response_disables_caching(self):
        self.assertEqual(
            image_response_headers(self.app),
            {
                "Cache-Control": "private, no-store",
                "Vary": "Origin, Referer",
            },
        )


class ImageDomainRouteTests(unittest.TestCase):
    def test_image_routes_enforce_domain_and_cache_policy(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            image_uuid = "1234567890abcdef1234567890abcdef"
            app = create_app(
                data_dir=temp_dir,
                allowed_image_domains=["example.com"],
            )
            image_path = image_disk_path(Path(temp_dir) / "images", image_uuid, "png")
            image_path.parent.mkdir(parents=True, exist_ok=True)
            image_path.write_bytes(
                b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
                b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
                b"\x1f\x15\xc4\x89\x00\x00\x00\rIDAT\x08\xd7c\xf8\xcf\xc0\xf0\x1f\x00\x05\x00\x01\xff"
                b"\x89\x99=\x1d\x00\x00\x00\x00IEND\xaeB`\x82"
            )

            denied, denied_headers, _ = request_app(app, f"/image/{image_uuid}")
            allowed, allowed_headers, _ = request_app(
                app,
                f"/image/{image_uuid}",
                [("Referer", "https://example.com/gallery")],
            )
            thumbnail, thumbnail_headers, _ = request_app(
                app,
                f"/thumbnail/{image_uuid}",
                [("Origin", "https://example.com")],
            )
            unrelated, _, _ = request_app(app, "/")
            download, _, _ = request_app(app, f"/download/{image_uuid}")

        self.assertEqual(denied, 403)
        self.assertEqual(denied_headers[b"cache-control"], b"private, no-store")
        self.assertEqual(allowed, 200)
        self.assertEqual(allowed_headers[b"cache-control"], b"private, no-store")
        self.assertEqual(allowed_headers[b"vary"], b"Origin, Referer")
        self.assertEqual(thumbnail, 200)
        self.assertEqual(thumbnail_headers[b"cache-control"], b"private, no-store")
        self.assertEqual(unrelated, 200)
        self.assertEqual(download, 401)

    def test_base_path_routes_enforce_domain(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            app = create_app(
                data_dir=temp_dir,
                base_path="/images",
                allowed_image_domains=["example.com"],
            )
            status_code, headers, _ = request_app(app, "/images/image/missing")

        self.assertEqual(status_code, 403)
        self.assertEqual(headers[b"cache-control"], b"private, no-store")


if __name__ == "__main__":
    unittest.main()
