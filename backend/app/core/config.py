"""Application settings, read from environment variables.

Secrets (API keys, added with CF-02) are only read from the environment and are
never stored in the repository (NFR-02).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]

'''
Application settings, read from environment variables.
Calculates Paths for the data directory and the dataset directory, which are used to store the database, uploaded files, and the benchmark dataset.
'''

@dataclass(frozen=True)
class Settings:
    # Writable runtime data: SQLite database and uploaded videos.
    data_dir: Path
    # Read-only benchmark dataset (testcases.csv + videos/) produced by dataset/generate.py.
    dataset_dir: Path
    max_upload_mb: int = 200

    @property
    def db_url(self) -> str:
        return f"sqlite:///{(self.data_dir / 'app.db').as_posix()}"

    @property
    def upload_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            data_dir=Path(os.getenv("DATA_DIR", BACKEND_DIR / "data")),
            dataset_dir=Path(os.getenv("DATASET_DIR", BACKEND_DIR.parent / "dataset")),
            max_upload_mb=int(os.getenv("MAX_UPLOAD_MB", "200")),
        )
