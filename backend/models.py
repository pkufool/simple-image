from sqlalchemy import create_engine, Column, String, DateTime, Text, ForeignKey, Integer, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from pathlib import Path
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 数据库配置
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "data" / "database.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}  # SQLite特定配置
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 图片-标签 多对多关联表
image_tag_association = Table(
    "image_tag_association",
    Base.metadata,
    Column("image_id", String, ForeignKey("images.id"), primary_key=True),
    Column("tag_id", String, ForeignKey("tags.id"), primary_key=True)
)

# 用户模型
class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True)  # 使用Logto的用户ID
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联图片
    images = relationship("Image", back_populates="owner")

# 标签模型
class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(String, primary_key=True, index=True)  # UUID
    name = Column(String, index=True)  # 标签名称
    owner_id = Column(String, ForeignKey("users.id"))  # 标签属于特定用户
    
    # 关联用户和图片
    owner = relationship("User", backref="tags")
    images = relationship(
        "Image",
        secondary=image_tag_association,
        back_populates="tags"
    )

# 图片模型
class Image(Base):
    __tablename__ = "images"
    
    id = Column(String, primary_key=True, index=True)  # UUID
    filename = Column(String, index=True)
    file_extension = Column(String)
    original_size = Column(Integer)  # 原始大小(字节)
    compressed_size = Column(Integer)  # 压缩后大小(字节)
    upload_time = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(String, ForeignKey("users.id"))
    
    # 关联用户和标签
    owner = relationship("User", back_populates="images")
    tags = relationship(
        "Tag",
        secondary=image_tag_association,
        back_populates="images"
    )

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
