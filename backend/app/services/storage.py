"""Storage of video files: resolving seed/upload paths and saving uploads."""

from __future__ import annotations

import hashlib # Calculation of SHA-256-checksum
from pathlib import Path #Filepath

from fastapi import UploadFile #FastAPI for uploaded files

from app.core.config import Settings #Configuration with dataset_dir and upload_dir
from app.models.testcase import TestCase, TestCaseSource

#Whitelist for technical specifications
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".mkv", ".avi"}
# Upload is read and written in 1 MiB chunks to keep memory usage constant
_CHUNK_SIZE = 1024 * 1024

#Custom exception for too large of an upload
class UploadTooLargeError(Exception):
    pass

'''
identifies the right path
'''
def video_path(tc: TestCase, settings: Settings) -> Path:
    root = settings.dataset_dir if tc.source == TestCaseSource.SEED else settings.upload_dir #selects the correct root folder. test cases are in dataset others are in the upload folder
    return root / tc.file #adds the filenames from the db


async def save_upload(upload: UploadFile, target: Path, max_bytes: int) -> str:
    """Streams the upload to `target` and returns its SHA-256.

    Removes the partial file if anything goes wrong (e.g. size limit exceeded).
    """
    # Make sure the target directory exists before opening the file
    target.parent.mkdir(parents=True, exist_ok=True)
    # The hash is computed incrementally while streaming so no second pass is needed
    hasher = hashlib.sha256()
    size = 0
    try:
        with target.open("wb") as out:
            #An empty chunk signals the end of the upload
            while chunk := await upload.read(_CHUNK_SIZE):
                size += len(chunk)
                if size > max_bytes:
                    raise UploadTooLargeError
                hasher.update(chunk)
                out.write(chunk)
    except BaseException:
        target.unlink(missing_ok=True)
        raise
    return hasher.hexdigest()
