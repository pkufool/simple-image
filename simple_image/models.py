from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    create_engine,
    event,
)
from sqlalchemy.engine import make_url
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.pool import QueuePool, StaticPool

Base = declarative_base()
DEFAULT_COMPRESS_QUALITY = 25

# 图片-标签 多对多关联表
image_tag_association = Table(
    "image_tag_association",
    Base.metadata,
    Column("image_id", String, ForeignKey("images.id"), primary_key=True),
    Column("tag_id", String, ForeignKey("tags.id"), primary_key=True)
)

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    password_hash = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    compress_enabled = Column(Boolean, default=True, nullable=False)
    compress_quality = Column(Integer, default=DEFAULT_COMPRESS_QUALITY, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    images = relationship("Image", back_populates="owner")

class Tag(Base):
    __tablename__ = "tags"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    owner_id = Column(String, ForeignKey("users.id"))

    owner = relationship("User", backref="tags")
    images = relationship(
        "Image",
        secondary=image_tag_association,
        back_populates="tags"
    )

class Image(Base):
    __tablename__ = "images"

    id = Column(String, primary_key=True, index=True)
    filename = Column(String, index=True)
    file_extension = Column(String)
    original_size = Column(Integer)
    compressed_size = Column(Integer)
    upload_time = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(String, ForeignKey("users.id"))

    owner = relationship("User", back_populates="images")
    tags = relationship(
        "Tag",
        secondary=image_tag_association,
        back_populates="images"
    )

class SessionToken(Base):
    __tablename__ = "session_tokens"

    token = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


def _normalize_database_url(database_url: str) -> str:
    # Allow shorthand mysql:// URLs by normalizing to SQLAlchemy driver URL.
    if database_url.startswith("mysql://"):
        return database_url.replace("mysql://", "mysql+pymysql://", 1)
    return database_url


def _is_sqlite_url(database_url: str) -> bool:
    return make_url(database_url).get_backend_name() == "sqlite"


def _is_sqlite_memory_url(database_url: str) -> bool:
    url = make_url(database_url)
    return _is_sqlite_url(database_url) and (
        url.database in (None, "", ":memory:") or url.query.get("mode") == "memory"
    )


def _configure_sqlite_connection(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA wal_autocheckpoint=1000")
        cursor.execute("PRAGMA journal_size_limit=67108864")
    finally:
        cursor.close()


def _enable_sqlite_wal(engine) -> None:
    try:
        with engine.connect() as connection:
            journal_mode = connection.exec_driver_sql("PRAGMA journal_mode=WAL").scalar_one()
    except Exception as exc:
        raise RuntimeError("Unable to enable SQLite WAL mode") from exc
    if str(journal_mode).lower() != "wal":
        raise RuntimeError(f"Unable to enable SQLite WAL mode (got {journal_mode!r})")


def _build_database_url(database_url: Optional[str], db_path: Optional[Path | str]) -> str:
    if database_url:
        return _normalize_database_url(database_url)
    if db_path is None:
        raise ValueError("Either database_url or db_path must be provided")
    sqlite_path = Path(db_path)
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{sqlite_path}"


def create_session_factory(
    default_compress_quality: int,
    database_url: Optional[str] = None,
    db_path: Optional[Path | str] = None,
):
    resolved_url = _build_database_url(database_url, db_path)
    engine_kwargs = {}
    is_sqlite = _is_sqlite_url(resolved_url)
    is_sqlite_memory = is_sqlite and _is_sqlite_memory_url(resolved_url)
    if is_sqlite:
        engine_kwargs["connect_args"] = {
            "check_same_thread": False,
            "timeout": 30,
        }
        if is_sqlite_memory:
            engine_kwargs["poolclass"] = StaticPool
        else:
            engine_kwargs.update(
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=5,
                pool_timeout=30,
                pool_use_lifo=True,
            )

    engine = create_engine(resolved_url, **engine_kwargs)
    if is_sqlite:
        event.listen(engine, "connect", _configure_sqlite_connection)
        if not is_sqlite_memory:
            _enable_sqlite_wal(engine)
    Base.metadata.create_all(bind=engine)

    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_from_session_local(session_local):
    db = session_local()
    try:
        yield db
    finally:
        db.close()
