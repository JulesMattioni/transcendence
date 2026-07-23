import os
import uuid
from app.config import UPLOAD_ROOT
from fastapi import UploadFile


class FileStorage:
    """
    Disk storage for uploaded binaries. The ONLY layer touching disk.

    Files are stored under <root>/org_<id>/<uuid><ext>: partitioned by
    organisation, named with a random UUID so original filenames never
    reach the filesystem.
    """

    def __init__(self, root: str = UPLOAD_ROOT) -> None:
        """
        Initialize the storage with its root directory.

        Args:
            root: Directory under which all binaries are stored.
        """

        self._root = root

    def build_path(self, organisation_id: int, original_filename: str) -> str:
        """
        Build a unique destination path, keeping only the extension.

        Args:
            organisation_id: Organisation owning the file, used as the
            subdirectory.
            original_filename: Client filename, only its extension is
            kept.

        Returns:
            Absolute destination path for the new binary.
        """

        _, ext = os.path.splitext(original_filename)
        unique_name = f"{uuid.uuid4().hex}{ext}"
        org_dir = os.path.join(self._root, f"org_{organisation_id}")
        return os.path.join(org_dir, unique_name)

    async def save(self, upload: UploadFile, destination: str) -> int:
        """
        Stream the upload to disk in 1 MB chunks.

        Args:
            upload: Uploaded binary content.
            destination: Target path, its directory is created if needed.

        Returns:
            The number of bytes written.
        """

        os.makedirs(os.path.dirname(destination), exist_ok=True)
        size = 0
        with open(destination, "wb") as out:
            while chunk := await upload.read(1024 * 1024):
                out.write(chunk)
                size += len(chunk)
        return size

    def delete(self, path: str) -> None:
        """
        Remove a file from disk; a missing file is not an error.

        Args:
            path: Path of the binary to remove.
        """

        try:
            os.remove(path)
        except FileNotFoundError:
            pass
