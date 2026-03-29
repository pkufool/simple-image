import os
from fastapi import Form, File, FastAPI, Depends, HTTPException, status, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_
from pydantic import BaseModel, Json
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import uuid

from models import get_db, User, Image, Tag
from utils import generate_uuid, compress_image, generate_uuid_filename
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
print (f"BASE DIR : {BASE_DIR}")
print (f"{Path(__file__)}")
IMAGES_DIR = BASE_DIR / "data" / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

API_URL = os.getenv("API_URL", "http://192.168.1.29:8000")

app = FastAPI(title="Simple Image API")

class UserCreate(BaseModel):
    id: str
    username: str
    email: str

class ImageInfo(BaseModel):
    id: str
    filename: str
    file_extension: str
    upload_time: datetime
    tags: List[str]
    owner_id: str
    original_size: int
    compressed_size: int

class TagUpdate(BaseModel):
    tags: List[str]

@app.post("/users/", response_model=UserCreate)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user.id).first()
    if db_user:
        return db_user
    
    db_user = User(
        id=user.id,
        username=user.username,
        email=user.email
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/upload")
def upload_image(
    file: UploadFile=File(...),
    data: Json=Form(),
    db: Session = Depends(get_db)
):
    # file = files[0]

    print (f"filename : {file.filename}")
    print (f"content type : {file.content_type}")
    print (f"json : {data}")
    # print (f"data : {len(file.file.read())}")

    user_id = data.get("user_id", None)
    tags = data.get("tags", [])

    try:
        file_extension = file.filename.rsplit(".", 1)[1]
        image_data = file.file.read()
        compressed_data, original_size, compressed_size = compress_image(
            image_data, file_extension
        )
    except Exception as e:
        print (f"Image processing error : {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image processing error: {str(e)}"
        )
    
    image_uuid = generate_uuid()
    image_path = IMAGES_DIR / f"{generate_uuid_filename(image_uuid)}.{file_extension}"
    print (f"image_path : {image_path}")
    image_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(image_path, "wb") as f:
        f.write(compressed_data)

    return {
        "id": "1234",
        "filename": file.filename,
        "url": f"{API_URL}/image/{image_uuid}",
        "message": "Image uploaded and compressed successfully"
    }


    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    tags = tags or []
    tag_objects = []
    
    for tag_name in tags:
        tag = db.query(Tag).filter(
            and_(Tag.name == tag_name, Tag.owner_id == user_id)
        ).first()
        
        if not tag:
            tag = Tag(
                id=str(uuid.uuid4()),
                name=tag_name,
                owner_id=user_id
            )
            db.add(tag)
        
        tag_objects.append(tag)
    
    filename = file.filename
    file_extension = filename.split(".")[-1].lower() if "." in filename else "jpg"
    
    try:
        image_data = file.file.read()
        compressed_data, original_size, compressed_size = compress_image(
            image_data, file_extension
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image processing error: {str(e)}"
        )
    
    image_uuid = generate_uuid()
    image_path = IMAGES_DIR / f"{image_uuid}.{file_extension}"
    
    with open(image_path, "wb") as f:
        f.write(compressed_data)
    
    db_image = Image(
        id=image_uuid,
        filename=filename,
        file_extension=file_extension,
        original_size=original_size,
        compressed_size=compressed_size,
        owner_id=user_id,
        tags=tag_objects
    )
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    
    return {
        "id": db_image.id,
        "filename": db_image.filename,
        "url": f"{os.getenv('API_URL')}/image/{db_image.id}",
        "message": "Image uploaded and compressed successfully"
    }

@app.get("/image/{image_uuid}", response_class=FileResponse)
def get_image(image_uuid: str, db: Session = Depends(get_db)):
    image_path = IMAGES_DIR / f"{generate_uuid_filename(image_uuid)}.jpg"
    # image_path = IMAGES_DIR / f"{image_uuid}.{db_image.file_extension}"
    print (f"image_path : {image_path}")
    if not image_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image file not found"
        )
    
    return image_path

    db_image = db.query(Image).filter(Image.id == image_uuid).first()
    if not db_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    

@app.get("/images/{user_id}", response_model=List[ImageInfo])
def get_user_images(
    user_id: str, 
    tag: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Image).filter(Image.owner_id == user_id)
    
    if tag:
        query = query.join(Image.tags).filter(
            and_(Tag.name == tag, Tag.owner_id == user_id)
        )
    
    images = query.order_by(Image.upload_time.desc()).all()
    
    result = []
    for img in images:
        result.append(ImageInfo(
            id=img.id,
            filename=img.filename,
            file_extension=img.file_extension,
            upload_time=img.upload_time,
            tags=[t.name for t in img.tags],
            owner_id=img.owner_id,
            original_size=img.original_size,
            compressed_size=img.compressed_size
        ))
    
    return result

@app.get("/tags/{user_id}")
def get_user_tags(user_id: str, db: Session = Depends(get_db)):
    tags = db.query(Tag).filter(Tag.owner_id == user_id).all()
    return [tag.name for tag in tags]

@app.put("/update-tags/{image_uuid}")
def update_tags(
    image_uuid: str,
    tag_update: TagUpdate,
    user_id: str,
    db: Session = Depends(get_db)
):
    db_image = db.query(Image).filter(Image.id == image_uuid).first()
    if not db_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    if db_image.owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this image"
        )
    
    new_tag_objects = []
    for tag_name in tag_update.tags:
        tag = db.query(Tag).filter(
            and_(Tag.name == tag_name, Tag.owner_id == user_id)
        ).first()
        
        if not tag:
            tag = Tag(
                id=str(uuid.uuid4()),
                name=tag_name,
                owner_id=user_id
            )
            db.add(tag)
        
        new_tag_objects.append(tag)
    
    db_image.tags = new_tag_objects
    db.commit()
    db.refresh(db_image)
    
    unused_tags = db.query(Tag).filter(
        and_(Tag.owner_id == user_id, ~Tag.images.any())
    ).all()
    for t in unused_tags:
        db.delete(t)
    db.commit()
    
    return {"status": "success", "tags": [t.name for t in db_image.tags]}

@app.delete("/delete-image/{image_uuid}")
def delete_image(
    image_uuid: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    db_image = db.query(Image).filter(Image.id == image_uuid).first()
    if not db_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    if db_image.owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this image"
        )
    
    associated_tags = db_image.tags
    
    image_path = IMAGES_DIR / f"{image_uuid}.{db_image.file_extension}"
    if image_path.exists():
        os.remove(image_path)
    
    db.delete(db_image)
    db.commit()
    
    for tag in associated_tags:
        if not tag.images:
            db.delete(tag)
    db.commit()
    
    return {"status": "success", "message": "Image deleted successfully"}
