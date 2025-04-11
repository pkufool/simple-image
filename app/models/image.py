from app import db
from .base import Base


class Image(Base):
    __tablename__: str = "image"
    name = db.Column(db.String(256), unique=True, nullable=False, comment="图片名称,长度为256")
    original_name = db.Column(db.String(256), nullable=True, comment="图片原始名称,长度为256")
    user_id = db.Column(db.Integer, nullable=True, comment="上传用户")

    def __str__(self):
        return self.name

    @staticmethod
    def create(name, original_name):
        image = Image()
        image.name = name
        image.original_name = original_name
        db.session.add(image)
        db.session.commit()
        return image

    def data(self):
        return {
            "name": self.name,
            "originalName": self.original_name,
        }
