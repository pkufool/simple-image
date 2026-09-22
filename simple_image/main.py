import hashlib
import html
import json
import mimetypes
import os
import secrets
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Sequence
from urllib.parse import urlsplit

from dotenv import load_dotenv
from fastapi import Cookie, Depends, FastAPI, File, Form, Header, HTTPException, Query, Request, Response, UploadFile, status
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

from pydantic import BaseModel, Field
from sqlalchemy import and_
from sqlalchemy.orm import Session

from .models import Image, SessionToken, Tag, User, create_session_factory
from .utils import compress_image, create_thumbnail, detect_image_extension, generate_uuid, generate_uuid_filename, normalize_image_extension

load_dotenv()

WEB_DIR = Path(__file__).parent / "web"
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "jpe", "jfif", "png", "gif", "webp"}
IMAGE_MEDIA_TYPES = {
    "jpeg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "webp": "image/webp",
}
TRANSCODE_ONLY_EXTENSIONS = {"heic", "heif", "jpeg"}
DEFAULT_COMPRESS_QUALITY = 25
SESSION_COOKIE_NAME = "simple_image_session"


class LoginRequest(BaseModel):
    username: str
    password: str


class UserPublic(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    is_admin: bool
    is_active: bool
    compress_enabled: bool
    compress_quality: int


class LoginResponse(BaseModel):
    user: UserPublic


class AdminCreateUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    email: Optional[str] = None


class AdminUpdatePasswordRequest(BaseModel):
    password: str = Field(min_length=6, max_length=128)


class AdminUpdateUploadSettingsRequest(BaseModel):
    compress_enabled: bool
    compress_quality: Optional[int] = Field(default=None, ge=1, le=95)


class ImageInfo(BaseModel):
    id: str
    filename: str
    file_extension: str
    upload_time: datetime
    tags: List[str]
    owner_id: str
    original_size: int
    compressed_size: int


class ImagePage(BaseModel):
    items: List[ImageInfo]
    total: int
    page: int
    page_size: int


class TagUpdate(BaseModel):
    tags: List[str]


def hash_password(password: str, salt: Optional[str] = None) -> str:
    use_salt = salt or secrets.token_hex(16)
    hashed = hashlib.sha256(f"{use_salt}:{password}".encode("utf-8")).hexdigest()
    return f"{use_salt}${hashed}"


def verify_password(password: str, password_hash: Optional[str]) -> bool:
    if not password_hash or "$" not in password_hash:
        return False
    salt, expected = password_hash.split("$", 1)
    hashed = hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()
    return secrets.compare_digest(hashed, expected)


def parse_tags(tags: List[str]) -> List[str]:
    cleaned = []
    seen = set()
    for raw in tags:
        tag = (raw or "").strip()
        if not tag or tag in seen:
            continue
        seen.add(tag)
        cleaned.append(tag)
    return cleaned


def parse_upload_month(value: Optional[str], field_name: str) -> Optional[datetime]:
    if value is None:
        return None
    try:
        return datetime.strptime(value, "%Y-%m")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid {field_name}") from exc


def next_month(value: datetime) -> datetime:
    return datetime(value.year + (value.month == 12), 1 if value.month == 12 else value.month + 1, 1)


def image_disk_path(images_dir: Path, image_id: str, extension: str) -> Path:
    return images_dir / f"{generate_uuid_filename(image_id)}.{extension}"


def find_image_file(images_dir: Path, image_id: str) -> Optional[Path]:
    """Locate an image on disk by scanning the directory, skipping the database."""
    base = images_dir / generate_uuid_filename(image_id)
    parent = base.parent
    if not parent.is_dir():
        return None
    stem = base.name
    for entry in parent.iterdir():
        if entry.is_file() and entry.stem == stem and entry.suffix.lstrip(".") in ALLOWED_EXTENSIONS:
            return entry
    return None


def normalize_path_prefix(value: Optional[str]) -> str:
    if not value:
        return ""
    prefix = value.strip()
    if not prefix:
        return ""
    if not prefix.startswith("/"):
        prefix = f"/{prefix}"
    return prefix.rstrip("/")


def _normalize_domain_name(value: str) -> str:
    domain = value.strip().rstrip(".")
    if not domain or any(char in domain for char in "/:@?#[]"):
        raise ValueError(f"Invalid allowed image domain: {value!r}")
    try:
        normalized = domain.encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise ValueError(f"Invalid allowed image domain: {value!r}") from exc
    if len(normalized) > 253:
        raise ValueError(f"Invalid allowed image domain: {value!r}")
    labels = normalized.split(".")
    if any(
        not label
        or len(label) > 63
        or label.startswith("-")
        or label.endswith("-")
        or not all(char.isalnum() or char == "-" for char in label)
        for label in labels
    ):
        raise ValueError(f"Invalid allowed image domain: {value!r}")
    return normalized


def normalize_allowed_image_domains(values: Optional[Sequence[str] | str]) -> tuple[str, ...]:
    if values is None:
        return ()
    raw_values = values.split(",") if isinstance(values, str) else values
    normalized = []
    seen = set()
    for raw_value in raw_values:
        value = str(raw_value).strip()
        if not value:
            continue
        wildcard = value.startswith("*.")
        wildcard_in_domain = "*" in (value[2:] if wildcard else value)
        if wildcard_in_domain:
            raise ValueError(f"Invalid allowed image domain: {raw_value!r}")
        domain = _normalize_domain_name(value[2:] if wildcard else value)
        rule = f"*.{domain}" if wildcard else domain
        if rule not in seen:
            seen.add(rule)
            normalized.append(rule)
    return tuple(normalized)


def image_domain_matches(hostname: str, allowed_domains: Sequence[str]) -> bool:
    try:
        normalized = _normalize_domain_name(hostname)
    except ValueError:
        return False
    for rule in allowed_domains:
        if rule.startswith("*."):
            suffix = rule[2:]
            if normalized.endswith(f".{suffix}"):
                return True
        elif normalized == rule:
            return True
    return False


def _source_hostname(value: str, is_origin: bool) -> Optional[str]:
    if not value or value.lower() == "null" or any(char in value for char in "\r\n"):
        return None
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return None
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        return None
    if parsed.username is not None or parsed.password is not None:
        return None
    if is_origin and (parsed.path not in {"", "/"} or parsed.query or parsed.fragment):
        return None
    if port is not None and not 1 <= port <= 65535:
        return None
    return parsed.hostname


def image_response_headers(app: FastAPI) -> dict[str, str]:
    if app.state.allowed_image_domains:
        return {
            "Cache-Control": "private, no-store",
            "Vary": "Origin, Referer",
        }
    return {"Cache-Control": "public, max-age=2592000"}


def enforce_image_domain(request: Request) -> None:
    allowed_domains = request.app.state.allowed_image_domains
    if not allowed_domains:
        return

    origins = request.headers.getlist("origin")
    referers = request.headers.getlist("referer")
    if origins:
        values = origins
        is_origin = True
    else:
        values = referers
        is_origin = False

    hostname = None
    if len(values) == 1 and "," not in values[0]:
        hostname = _source_hostname(values[0].strip(), is_origin=is_origin)
    if not hostname or not image_domain_matches(hostname, allowed_domains):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Image source is not allowed",
            headers={
                "Cache-Control": "private, no-store",
                "Vary": "Origin, Referer",
            },
        )


def render_index_html(app: FastAPI) -> HTMLResponse:
    index_file = WEB_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Frontend not built")

    template = getattr(app.state, "index_html_template", None)
    if template is None:
        template = index_file.read_text(encoding="utf-8")
        app.state.index_html_template = template

    public_url = (app.state.api_url or "").rstrip("/")
    rendered = template.replace("__SIMPLE_IMAGE_BASE_PATH__", app.state.base_path)
    rendered = rendered.replace(
        "__SIMPLE_IMAGE_PUBLIC_URL__",
        html.escape(public_url, quote=True),
    )
    return HTMLResponse(content=rendered)


def get_public_base_url(request: Request, app: FastAPI) -> str:
    # API_URL has the highest priority when explicitly configured.
    configured = (app.state.api_url or "").rstrip("/")
    if configured:
        return configured

    request_base = str(request.base_url).rstrip("/")
    for prefix in (
        normalize_path_prefix(request.headers.get("x-forwarded-prefix")),
        normalize_path_prefix(getattr(app.state, "base_path", "")),
    ):
        if prefix and not request_base.endswith(prefix):
            request_base = f"{request_base}{prefix}"
    return request_base


def to_user_public(user: User) -> UserPublic:
    return UserPublic(
        id=user.id,
        username=user.username,
        email=user.email,
        is_admin=bool(user.is_admin),
        is_active=bool(user.is_active),
        compress_enabled=bool(user.compress_enabled),
        compress_quality=int(user.compress_quality or DEFAULT_COMPRESS_QUALITY),
    )


def get_db(request: Request):
    session_local = request.app.state.session_local
    db = session_local()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db),
    session_token: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    authorization: Optional[str] = Header(default=None),
) -> User:
    token = session_token or ""
    if not token and authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    session = db.query(SessionToken).filter(SessionToken.token == token).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.query(User).filter(User.id == session.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user")

    return user


def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return current_user


def _bootstrap_admin(app: FastAPI) -> None:
    session_local = app.state.session_local
    db = session_local()
    try:
        admin = db.query(User).filter(User.username == app.state.admin_username).first()
        if admin:
            return
        db.add(
            User(
                id=generate_uuid(),
                username=app.state.admin_username,
                email=None,
                password_hash=hash_password(app.state.admin_password),
                is_admin=True,
                is_active=True,
                compress_enabled=True,
                compress_quality=app.state.default_compress_quality,
            )
        )
        db.commit()
    finally:
        db.close()


def create_app(
    data_dir: Path | str | None = None,
    api_url: Optional[str] = None,
    admin_username: Optional[str] = None,
    admin_password: Optional[str] = None,
    default_compress_quality: Optional[int] = None,
    database_url: Optional[str] = None,
    base_path: Optional[str] = None,
    allowed_image_domains: Optional[Sequence[str]] = None,
) -> FastAPI:
    base_data_dir = Path(data_dir) if data_dir else Path(os.getenv("SIMPLE_IMAGE_DATA_DIR", "data"))
    base_data_dir.mkdir(parents=True, exist_ok=True)

    default_quality = int(default_compress_quality or os.getenv("IMAGE_COMPRESS_QUALITY", 25))
    resolved_base_path = normalize_path_prefix(
        base_path if base_path is not None else os.getenv("SIMPLE_IMAGE_BASE_PATH") or os.getenv("BASE_PATH")
    )
    configured_image_domains = (
        allowed_image_domains
        if allowed_image_domains is not None
        else os.getenv("SIMPLE_IMAGE_ALLOWED_DOMAINS")
    )

    app = FastAPI(title="Simple Image API")
    app.state.data_dir = base_data_dir
    app.state.images_dir = base_data_dir / "images"
    app.state.images_dir.mkdir(parents=True, exist_ok=True)
    app.state.api_url = api_url or os.getenv("API_URL")
    app.state.allowed_image_domains = normalize_allowed_image_domains(configured_image_domains)
    app.state.admin_username = admin_username or os.getenv("ADMIN_USERNAME", "admin")
    app.state.admin_password = admin_password or os.getenv("ADMIN_PASSWORD", "admin123456")
    app.state.default_compress_quality = max(1, min(95, default_quality))
    app.state.session_cookie_samesite = os.getenv("SESSION_COOKIE_SAMESITE", "lax")
    app.state.session_cookie_secure = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    app.state.session_cookie_domain = os.getenv("SESSION_COOKIE_DOMAIN") or None
    app.state.base_path = resolved_base_path
    app.state.session_cookie_path = os.getenv("SESSION_COOKIE_PATH") or (resolved_base_path or "/")
    app.state.session_max_age = int(os.getenv("SESSION_MAX_AGE", "604800"))
    app.state.database_url = database_url or os.getenv("SIMPLE_IMAGE_DATABASE_URL") or os.getenv("DATABASE_URL")
    app.state.db_path = base_data_dir / "database.db"
    app.state.session_local = create_session_factory(
        default_compress_quality=app.state.default_compress_quality,
        database_url=app.state.database_url,
        db_path=None if app.state.database_url else app.state.db_path,
    )

    _bootstrap_admin(app)
    _register_routes(app)
    if not resolved_base_path:
        return app

    container = FastAPI(title="Simple Image", docs_url=None, redoc_url=None, openapi_url=None)

    @container.get(resolved_base_path, include_in_schema=False)
    def _redirect_base_path_entry():
        return RedirectResponse(url=f"{resolved_base_path}/", status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    container.mount(resolved_base_path, app)
    return container


def _register_routes(app: FastAPI) -> None:

    @app.post("/auth/login", response_model=LoginResponse)
    def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
        user = db.query(User).filter(User.username == payload.username).first()
        if not user or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is disabled")

        token = secrets.token_urlsafe(32)
        db.add(SessionToken(token=token, user_id=user.id))
        db.commit()
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=token,
            httponly=True,
            secure=app.state.session_cookie_secure,
            samesite=app.state.session_cookie_samesite,
            domain=app.state.session_cookie_domain,
            path=app.state.session_cookie_path,
            max_age=app.state.session_max_age,
        )
        return LoginResponse(user=to_user_public(user))


    @app.post("/auth/logout")
    def logout(
        response: Response,
        db: Session = Depends(get_db),
        session_token: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE_NAME),
        authorization: Optional[str] = Header(default=None),
    ):
        token = session_token or ""
        if not token and authorization and authorization.startswith("Bearer "):
            token = authorization.split(" ", 1)[1].strip()
        if token:
            db.query(SessionToken).filter(SessionToken.token == token).delete()
            db.commit()
        response.delete_cookie(
            key=SESSION_COOKIE_NAME,
            domain=app.state.session_cookie_domain,
            path=app.state.session_cookie_path,
        )
        return {"status": "success"}


    @app.get("/auth/me", response_model=UserPublic)
    def me(current_user: User = Depends(get_current_user)):
        return to_user_public(current_user)


    @app.get("/admin/users", response_model=List[UserPublic])
    def admin_list_users(
        db: Session = Depends(get_db),
        _: User = Depends(get_admin_user),
    ):
        users = db.query(User).order_by(User.created_at.asc()).all()
        return [to_user_public(user) for user in users]


    @app.post("/admin/users", response_model=UserPublic)
    def admin_create_user(
        payload: AdminCreateUserRequest,
        db: Session = Depends(get_db),
        _: User = Depends(get_admin_user),
    ):
        existing = db.query(User).filter(User.username == payload.username).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
        if payload.email:
            existing_email = db.query(User).filter(User.email == payload.email).first()
            if existing_email:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

        user = User(
            id=generate_uuid(),
            username=payload.username,
            email=payload.email,
            password_hash=hash_password(payload.password),
            is_admin=False,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return to_user_public(user)


    @app.put("/admin/users/{user_id}/password")
    def admin_update_password(
        user_id: str,
        payload: AdminUpdatePasswordRequest,
        db: Session = Depends(get_db),
        _: User = Depends(get_admin_user),
    ):
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        user.password_hash = hash_password(payload.password)
        db.query(SessionToken).filter(SessionToken.user_id == user.id).delete()
        db.commit()
        return {"status": "success"}


    @app.put("/admin/users/{user_id}/upload-settings", response_model=UserPublic)
    def admin_update_upload_settings(
        user_id: str,
        payload: AdminUpdateUploadSettingsRequest,
        db: Session = Depends(get_db),
        _: User = Depends(get_admin_user),
    ):
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if payload.compress_enabled and payload.compress_quality is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="compress_quality is required when compression is enabled")

        user.compress_enabled = payload.compress_enabled
        if payload.compress_quality is not None:
            user.compress_quality = payload.compress_quality
        elif not user.compress_quality:
            user.compress_quality = app.state.default_compress_quality

        db.commit()
        db.refresh(user)
        return to_user_public(user)


    @app.post("/upload")
    def upload_image(
        request: Request,
        file: UploadFile = File(...),
        tags: Optional[str] = Form(default=None),
        data: Optional[str] = Form(default=None),
        client_original_size: Optional[int] = Form(default=None, ge=1),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        image_data = file.file.read()
        if not image_data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty image file")

        try:
            detected_extension = detect_image_extension(image_data)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

        extension = normalize_image_extension(detected_extension)
        if extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported image type")

        parsed_tags: List[str] = []
        if tags:
            try:
                payload_tags = json.loads(tags)
                if not isinstance(payload_tags, list):
                    raise ValueError("tags must be a list")
                parsed_tags = parse_tags(payload_tags)
            except (json.JSONDecodeError, ValueError):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid tags payload")
        elif data:
            try:
                payload = json.loads(data)
                raw_tags = payload.get("tags", [])
                if not isinstance(raw_tags, list):
                    raise ValueError("tags must be a list")
                parsed_tags = parse_tags(raw_tags)
            except (json.JSONDecodeError, ValueError):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid tags payload")

        try:
            received_size = len(image_data)
            is_client_compressed = client_original_size is not None and client_original_size != received_size
            original_size = client_original_size if is_client_compressed else received_size
            needs_transcode = detected_extension in TRANSCODE_ONLY_EXTENSIONS
            if is_client_compressed:
                stored_data = image_data
                compressed_size = received_size
                upload_message = "Image uploaded with client-side compression"
            elif current_user.compress_enabled or needs_transcode:
                output_quality = current_user.compress_quality if current_user.compress_enabled else 95
                compressed_data, _, compressed_size = compress_image(
                    image_data,
                    extension,
                    quality=output_quality,
                )
                stored_data = compressed_data
                if current_user.compress_enabled:
                    upload_message = "Image uploaded and compressed successfully"
                else:
                    upload_message = "Image uploaded successfully (converted from HEIC/HEIF for compatibility)"
            else:
                stored_data = image_data
                compressed_size = original_size
                upload_message = "Image uploaded successfully (compression disabled for this user)"
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Image processing error: {str(exc)}",
            )

        tag_objects = []
        for tag_name in parsed_tags:
            tag = db.query(Tag).filter(and_(Tag.name == tag_name, Tag.owner_id == current_user.id)).first()
            if not tag:
                tag = Tag(id=generate_uuid(), name=tag_name, owner_id=current_user.id)
                db.add(tag)
            tag_objects.append(tag)

        image_uuid = generate_uuid()
        image_path = image_disk_path(app.state.images_dir, image_uuid, extension)
        image_path.parent.mkdir(parents=True, exist_ok=True)
        with open(image_path, "wb") as image_file:
            image_file.write(stored_data)

        db_image = Image(
            id=image_uuid,
            filename=file.filename,
            file_extension=extension,
            original_size=original_size,
            compressed_size=compressed_size,
            owner_id=current_user.id,
            tags=tag_objects,
        )
        db.add(db_image)
        db.commit()
        db.refresh(db_image)

        url_base = get_public_base_url(request, app)

        return {
            "id": db_image.id,
            "filename": db_image.filename,
            "url": f"{url_base}/image/{db_image.id}",
            "message": upload_message,
        }


    @app.get("/image/{image_uuid}", response_class=FileResponse)
    def get_image(image_uuid: str, _: None = Depends(enforce_image_domain)):
        image_path = find_image_file(app.state.images_dir, image_uuid)
        if not image_path:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
        ext = normalize_image_extension(image_path.suffix.lstrip("."))
        media_type = IMAGE_MEDIA_TYPES.get(ext, "application/octet-stream")
        return FileResponse(path=image_path, media_type=media_type, headers=image_response_headers(app))
        # db_image = db.query(Image).filter(Image.id == image_uuid).first()
        # if not db_image:
        #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
        # image_path = image_disk_path(app.state.images_dir, db_image.id, db_image.file_extension)
        # if not image_path.exists():
        #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image file not found")
        # media_type = IMAGE_MEDIA_TYPES.get(normalize_image_extension(db_image.file_extension), "application/octet-stream")
        # return FileResponse(path=image_path, media_type=media_type)


    @app.get("/download/{image_uuid}")
    def download_image(
        image_uuid: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        db_image = db.query(Image).filter(Image.id == image_uuid).first()
        if not db_image:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
        if db_image.owner_id != current_user.id and not current_user.is_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission to download this image")

        image_path = image_disk_path(app.state.images_dir, db_image.id, db_image.file_extension)
        if not image_path.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image file not found")

        media_type = IMAGE_MEDIA_TYPES.get(normalize_image_extension(db_image.file_extension), "application/octet-stream")
        return FileResponse(path=image_path, media_type=media_type, filename=db_image.filename)


    @app.get("/thumbnail/{image_uuid}")
    def get_thumbnail(
        image_uuid: str,
        size: int = Query(default=160, ge=48, le=512),
        quality: int = Query(default=75, ge=40, le=95),
        _: None = Depends(enforce_image_domain),
    ):
        image_path = find_image_file(app.state.images_dir, image_uuid)
        if not image_path:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")

        try:
            with open(image_path, "rb") as source_file:
                image_data = source_file.read()
            thumbnail_data = create_thumbnail(image_data=image_data, size=size, quality=quality)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Thumbnail generation error: {str(exc)}")

        return Response(
            content=thumbnail_data,
            media_type="image/jpeg",
            headers=image_response_headers(app),
        )
        # db_image = db.query(Image).filter(Image.id == image_uuid).first()
        # if not db_image:
        #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
        # image_path = image_disk_path(app.state.images_dir, db_image.id, db_image.file_extension)
        # if not image_path.exists():
        #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image file not found")


    def list_user_images(
        owner_id: str,
        tag: Optional[str],
        upload_month_start: Optional[str],
        upload_month_end: Optional[str],
        db: Session,
    ):
        query = db.query(Image).filter(Image.owner_id == owner_id)
        if tag:
            query = query.join(Image.tags).filter(and_(Tag.name == tag, Tag.owner_id == owner_id))
        start = parse_upload_month(upload_month_start, "upload_month_start")
        end = parse_upload_month(upload_month_end, "upload_month_end")
        if start and end and start > end:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid upload month range")
        if start:
            query = query.filter(Image.upload_time >= start)
        if end:
            query = query.filter(Image.upload_time < next_month(end))

        images = query.order_by(Image.upload_time.desc()).all()
        return [
            ImageInfo(
                id=img.id,
                filename=img.filename,
                file_extension=img.file_extension,
                upload_time=img.upload_time,
                tags=[t.name for t in img.tags],
                owner_id=img.owner_id,
                original_size=img.original_size,
                compressed_size=img.compressed_size,
            )
            for img in images
        ]


    def list_user_images_page(
        owner_id: str,
        tag: Optional[str],
        upload_month_start: Optional[str],
        upload_month_end: Optional[str],
        page: int,
        page_size: int,
        db: Session,
    ) -> ImagePage:
        query = db.query(Image).filter(Image.owner_id == owner_id)
        if tag:
            query = query.join(Image.tags).filter(and_(Tag.name == tag, Tag.owner_id == owner_id))
        start = parse_upload_month(upload_month_start, "upload_month_start")
        end = parse_upload_month(upload_month_end, "upload_month_end")
        if start and end and start > end:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid upload month range")
        if start:
            query = query.filter(Image.upload_time >= start)
        if end:
            query = query.filter(Image.upload_time < next_month(end))

        total = query.count()
        offset = (page - 1) * page_size
        images = query.order_by(Image.upload_time.desc()).offset(offset).limit(page_size).all()
        items = [
            ImageInfo(
                id=img.id,
                filename=img.filename,
                file_extension=img.file_extension,
                upload_time=img.upload_time,
                tags=[t.name for t in img.tags],
                owner_id=img.owner_id,
                original_size=img.original_size,
                compressed_size=img.compressed_size,
            )
            for img in images
        ]
        return ImagePage(items=items, total=total, page=page, page_size=page_size)


    @app.get("/images/me", response_model=List[ImageInfo])
    def get_my_images(
        tag: Optional[str] = None,
        upload_month_start: Optional[str] = None,
        upload_month_end: Optional[str] = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        return list_user_images(current_user.id, tag, upload_month_start, upload_month_end, db)


    @app.get("/images/me/page", response_model=ImagePage)
    def get_my_images_page(
        tag: Optional[str] = None,
        upload_month_start: Optional[str] = None,
        upload_month_end: Optional[str] = None,
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=20, ge=1, le=100),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        return list_user_images_page(current_user.id, tag, upload_month_start, upload_month_end, page, page_size, db)


    @app.get("/images/{user_id}", response_model=List[ImageInfo])
    def get_user_images(
        user_id: str,
        tag: Optional[str] = None,
        upload_month_start: Optional[str] = None,
        upload_month_end: Optional[str] = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        if user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        return list_user_images(user_id, tag, upload_month_start, upload_month_end, db)


    @app.get("/images/{user_id}/page", response_model=ImagePage)
    def get_user_images_page(
        user_id: str,
        tag: Optional[str] = None,
        upload_month_start: Optional[str] = None,
        upload_month_end: Optional[str] = None,
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=20, ge=1, le=100),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        if user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        return list_user_images_page(user_id, tag, upload_month_start, upload_month_end, page, page_size, db)


    @app.get("/tags/me")
    def get_my_tags(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        tags = db.query(Tag).filter(Tag.owner_id == current_user.id).order_by(Tag.name.asc()).all()
        return [tag.name for tag in tags]


    @app.get("/tags/{user_id}")
    def get_user_tags(
        user_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        if user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        tags = db.query(Tag).filter(Tag.owner_id == user_id).order_by(Tag.name.asc()).all()
        return [tag.name for tag in tags]


    @app.put("/update-tags/{image_uuid}")
    def update_tags(
        image_uuid: str,
        tag_update: TagUpdate,
        user_id: Optional[str] = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        db_image = db.query(Image).filter(Image.id == image_uuid).first()
        if not db_image:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")

        if db_image.owner_id != current_user.id and not current_user.is_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this image")
        if user_id and user_id != db_image.owner_id and not current_user.is_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        new_tag_objects = []
        for tag_name in parse_tags(tag_update.tags):
            tag = db.query(Tag).filter(and_(Tag.name == tag_name, Tag.owner_id == db_image.owner_id)).first()
            if not tag:
                tag = Tag(id=generate_uuid(), name=tag_name, owner_id=db_image.owner_id)
                db.add(tag)
            new_tag_objects.append(tag)

        db_image.tags = new_tag_objects
        db.commit()
        db.refresh(db_image)

        unused_tags = db.query(Tag).filter(and_(Tag.owner_id == db_image.owner_id, ~Tag.images.any())).all()
        for item in unused_tags:
            db.delete(item)
        db.commit()

        return {"status": "success", "tags": [t.name for t in db_image.tags]}


    @app.delete("/delete-image/{image_uuid}")
    def delete_image(
        image_uuid: str,
        user_id: Optional[str] = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        db_image = db.query(Image).filter(Image.id == image_uuid).first()
        if not db_image:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")

        if db_image.owner_id != current_user.id and not current_user.is_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this image")
        if user_id and user_id != db_image.owner_id and not current_user.is_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        associated_tags = list(db_image.tags)
        image_path = image_disk_path(app.state.images_dir, db_image.id, db_image.file_extension)
        if image_path.exists():
            os.remove(image_path)

        db.delete(db_image)
        db.commit()

        for tag in associated_tags:
            if not tag.images:
                db.delete(tag)
        db.commit()
        return {"status": "success", "message": "Image deleted successfully"}


    if WEB_DIR.exists():
        static_dir = WEB_DIR / "static"
        if static_dir.exists():

            @app.get("/static/{file_path:path}", include_in_schema=False)
            def static_file(file_path: str):
                full_path = static_dir / file_path
                if not full_path.exists() or not full_path.is_file():
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
                media_type = mimetypes.guess_type(str(full_path))[0]
                return FileResponse(
                    path=full_path,
                    media_type=media_type,
                    headers={"Cache-Control": "public, max-age=604800"},
                )


    @app.get("/", include_in_schema=False)
    def web_root():
        return render_index_html(app)


    @app.get("/{full_path:path}", include_in_schema=False)
    def web_fallback(full_path: str):
        if full_path.startswith(("auth/", "admin/", "image/", "thumbnail/", "images/", "upload", "tags/", "update-tags/", "delete-image/", "docs", "openapi.json", "redoc")):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

        index_file = WEB_DIR / "index.html"
        file_path = WEB_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        if index_file.exists():
            return render_index_html(app)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Frontend not built")
