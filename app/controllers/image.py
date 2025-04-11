from datetime import timedelta
import base64
import logging
import string
import random
import time
from flask import Blueprint, jsonify, request, render_template, send_from_directory
from app import db
from app.utils.responses import response_with
from app.utils import responses as resp
from app.models.image import Image
import os
import uuid
from pathlib import Path
from config import basedir

image_bp = Blueprint("image", __name__)

pwd = os.path.dirname(__file__)


def get_filename(unique_id: str):
    return f"{unique_id[20:32]}/{unique_id[8:20]}/{unique_id}"


@image_bp.route("/", methods=["GET"])
def home():
    return render_template("image.html")


@image_bp.route("/f/<path:name>", methods=["GET"])
def send_file_by_name(name):
    dirname = Path(get_filename(name)).parent
    root = Path(basedir) / "data" / dirname
    return send_from_directory(root, name, as_attachment=False)


@image_bp.route("/upload", methods=["POST"])
def upload():
    files = request.files.getlist("file_data")
    uploaded_filenames = []
    for file in files:
        if file:
            file_extension = os.path.splitext(file.filename)[1]
            unique_id = uuid.uuid1().hex
            unique_filename = (
                Path(basedir) / "data" / Path(get_filename(unique_id) + file_extension)
            )
            unique_filename.parent.mkdir(parents=True, exist_ok=True)
            file.save(unique_filename)
            uploaded_filenames.append(unique_filename.name)

    return jsonify({"message": "图片上传成功", "filenames": uploaded_filenames})
