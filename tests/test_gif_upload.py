import asyncio
import io
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image as PILImage

from simple_image.main import create_app, find_image_file
from simple_image.utils import compress_image, is_animated_image


def request_app(app, method, path, body=None, headers=()):
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


def build_multipart(fields, files, boundary="----simpleimageboundary"):
    """files: list of (field_name, filename, content_type, payload)."""
    parts = []
    for name, value in fields.items():
        parts.append(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
            f"{value}\r\n".encode("utf-8")
        )
    for field_name, filename, content_type, payload in files:
        parts.append(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n".encode("utf-8")
        )
        parts.append(payload)
        parts.append(b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def make_animated_gif(frame_count=3, size=(32, 24)):
    frames = [
        PILImage.new("RGB", size, (40 * index, 90, 200)) for index in range(frame_count)
    ]
    buffer = io.BytesIO()
    frames[0].save(
        buffer,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=100,
        loop=0,
    )
    return buffer.getvalue()


def make_static_jpeg(size=(64, 48)):
    buffer = io.BytesIO()
    PILImage.new("RGB", size, (200, 30, 30)).save(buffer, format="JPEG")
    return buffer.getvalue()


def frames_of(image_data):
    image = PILImage.open(io.BytesIO(image_data))
    return int(getattr(image, "n_frames", 1) or 1)


class AnimatedImageDetectionTests(unittest.TestCase):
    def test_detects_animated_gif_and_rejects_static_images(self):
        self.assertTrue(is_animated_image(make_animated_gif(3)))
        self.assertFalse(is_animated_image(make_animated_gif(1)))
        self.assertFalse(is_animated_image(make_static_jpeg()))

    def test_compress_image_flattens_animation(self):
        # Documents why uploads must skip compression for animated images:
        # re-encoding keeps only the first frame.
        gif_bytes = make_animated_gif(3)
        compressed, _, _ = compress_image(gif_bytes, "gif", quality=80)
        self.assertEqual(frames_of(gif_bytes), 3)
        self.assertEqual(frames_of(compressed), 1)


class AnimatedGifUploadTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.app = create_app(data_dir=Path(self._tmp.name))
        self.engine = self.app.state.session_local.kw["bind"]

        status, headers, _ = request_app(
            self.app,
            "POST",
            "/auth/login",
            json.dumps({"username": "admin", "password": "admin123456"}).encode("utf-8"),
            [("Content-Type", "application/json")],
        )
        self.assertEqual(status, 200)
        self.cookie = headers[b"set-cookie"].decode("utf-8").split(";", 1)[0]

    def tearDown(self):
        self.engine.dispose()
        self._tmp.cleanup()

    def upload(self, payload, filename, content_type, extra_fields=None):
        fields = {"tags": "[]"}
        fields.update(extra_fields or {})
        body, content_header = build_multipart(
            fields,
            [("file", filename, content_type, payload)],
        )
        status, _, response = request_app(
            self.app,
            "POST",
            "/upload",
            body,
            [("Content-Type", content_header), ("Cookie", self.cookie)],
        )
        return status, json.loads(response)

    def test_animated_gif_is_stored_untouched(self):
        gif_bytes = make_animated_gif(3)
        status, data = self.upload(
            gif_bytes,
            "anim.gif",
            "image/gif",
            # Equal to the payload size, i.e. no client-side compression:
            # this is exactly the branch that used to re-encode and flatten.
            extra_fields={"client_original_size": str(len(gif_bytes))},
        )
        self.assertEqual(status, 200)
        self.assertIn("as-is", data["message"])

        stored_path = find_image_file(self.app.state.images_dir, data["id"])
        self.assertIsNotNone(stored_path)
        self.assertEqual(stored_path.suffix, ".gif")
        self.assertEqual(stored_path.read_bytes(), gif_bytes)
        self.assertEqual(frames_of(stored_path.read_bytes()), 3)

    def test_animated_gif_stays_animated_on_image_and_thumbnail_routes(self):
        gif_bytes = make_animated_gif(3)
        status, data = self.upload(gif_bytes, "anim.gif", "image/gif")
        self.assertEqual(status, 200)

        image_status, image_headers, image_body = request_app(
            self.app, "GET", f"/image/{data['id']}"
        )
        self.assertEqual(image_status, 200)
        self.assertEqual(image_headers[b"content-type"], b"image/gif")
        self.assertEqual(image_body, gif_bytes)

        thumb_status, thumb_headers, thumb_body = request_app(
            self.app, "GET", f"/thumbnail/{data['id']}"
        )
        self.assertEqual(thumb_status, 200)
        self.assertEqual(thumb_headers[b"content-type"], b"image/gif")
        self.assertEqual(thumb_body, gif_bytes)

    def test_static_images_keep_normal_thumbnails(self):
        jpeg_bytes = make_static_jpeg()
        status, data = self.upload(jpeg_bytes, "photo.jpg", "image/jpeg")
        self.assertEqual(status, 200)

        thumb_status, thumb_headers, thumb_body = request_app(
            self.app, "GET", f"/thumbnail/{data['id']}"
        )
        self.assertEqual(thumb_status, 200)
        self.assertEqual(thumb_headers[b"content-type"], b"image/jpeg")
        self.assertEqual(frames_of(thumb_body), 1)


if __name__ == "__main__":
    unittest.main()
