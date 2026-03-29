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
    inspect,
    text,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

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


def _get_columns(connection, table_name: str) -> set[str]:
    rows = connection.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
    return {row[1] for row in rows}


def ensure_schema_compatibility(engine, default_compress_quality: int) -> None:
    with engine.begin() as connection:
        user_columns = _get_columns(connection, "users")
        if "password_hash" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR"))
        if "is_admin" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT 0"))
        if "is_active" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1"))
        if "compress_enabled" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN compress_enabled BOOLEAN NOT NULL DEFAULT 1"))
        if "compress_quality" not in user_columns:
            connection.execute(
                text(
                    "ALTER TABLE users ADD COLUMN compress_quality "
                    f"INTEGER NOT NULL DEFAULT {default_compress_quality}"
                )
            )


def _normalize_database_url(database_url: str) -> str:
    # Allow shorthand mysql:// URLs by normalizing to SQLAlchemy driver URL.
    if database_url.startswith("mysql://"):
        return database_url.replace("mysql://", "mysql+pymysql://", 1)
    return database_url


def _is_sqlite_url(database_url: str) -> bool:
    return database_url.startswith("sqlite://")


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
    if _is_sqlite_url(resolved_url):
        engine_kwargs["connect_args"] = {"check_same_thread": False}

    engine = create_engine(resolved_url, **engine_kwargs)
    Base.metadata.create_all(bind=engine)

    if _is_sqlite_url(resolved_url) and inspect(engine).has_table("users"):
        ensure_schema_compatibility(engine, default_compress_quality)

    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_from_session_local(session_local):
    db = session_local()
    try:
        yield db
    finally:
        db.close()
