import os
import uuid
from pathlib import Path

from werkzeug.utils import secure_filename

from .errors import ApiError


def save_image(file_storage, upload_folder, allowed_extensions):
    if not file_storage or not file_storage.filename:
        raise ApiError("Необходимо загрузить изображение.", 400)

    filename = secure_filename(file_storage.filename)
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension not in allowed_extensions:
        raise ApiError("Неподдерживаемый тип изображения.", 400)

    Path(upload_folder).mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}.{extension}"
    file_path = Path(upload_folder) / stored_name
    file_storage.save(file_path)
    return f"/uploads/{stored_name}"


def remove_local_image(image_url, upload_folder):
    if not image_url or not image_url.startswith("/uploads/"):
        return

    filename = image_url.split("/uploads/", 1)[1]
    file_path = Path(upload_folder) / filename
    if file_path.exists() and file_path.is_file():
        os.remove(file_path)
