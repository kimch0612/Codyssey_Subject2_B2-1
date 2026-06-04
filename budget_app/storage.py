"""File storage, serialization, and deserialization helpers."""

from __future__ import annotations

from pathlib import Path


DEFAULT_DATA_DIR = Path("data")


def get_data_dir(data_dir: str | Path = DEFAULT_DATA_DIR) -> Path:
    return Path(data_dir)

