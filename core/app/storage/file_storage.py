import os
import uuid
from app.config import UPLOAD_ROOT
from fastapi import UploadFile


class FileStorage:
    def __init__(self, root: str = UPLOAD_ROOT) -> None:
        self._root = root

    def build_path(self, organisation_id: int, original_filename: str) -> str:
        _, ext = os.path.splitext(original_filename)
        unique_name = f"{uuid.uuid4().hex}{ext}"
        org_dir = os.path.join(self._root, f"org_{organisation_id}")
        return os.path.join(org_dir, unique_name)

    async def save(self, upload: UploadFile, destination: str) -> int:
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        size = 0
        with open(destination, "wb") as out:
            while chunk := await upload.read(1024 * 1024):
                out.write(chunk)
                size += len(chunk)
        return size

    def delete(self, path: str) -> None:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
