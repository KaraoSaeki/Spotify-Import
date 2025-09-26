from __future__ import annotations

import csv
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

from .utils import ensure_dir, now_timestamp_str


def setup_logging() -> tuple[logging.Logger, Path]:
    """Initialize logging to console (INFO) and file per run.

    Returns (logger, log_file_path)
    """
    ts = now_timestamp_str()
    logs_dir = Path("logs")
    ensure_dir(logs_dir)
    log_path = logs_dir / f"spotify-import-{ts}.log"

    logger = logging.getLogger("spotify_importer")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch_fmt = logging.Formatter("%(levelname)s | %(message)s")
    ch.setFormatter(ch_fmt)
    logger.addHandler(ch)

    # File handler
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh_fmt = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    fh.setFormatter(fh_fmt)
    logger.addHandler(fh)

    logger.debug("Logging initialized")
    return logger, log_path


def init_summaries() -> tuple[Path, Path]:
    ts = now_timestamp_str()
    reports_dir = Path("reports")
    ensure_dir(reports_dir)
    csv_path = reports_dir / f"summary-{ts}.csv"
    json_path = reports_dir / f"summary-{ts}.json"
    # Create empty files
    csv_path.touch()
    json_path.touch()
    return csv_path, json_path


def _csv_write_header_if_empty(csv_path: Path, fieldnames: list[str]) -> None:
    if csv_path.stat().st_size == 0:
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()


def write_summary_row(csv_path: Path, json_path: Path, row: Dict[str, Any]) -> None:
    """Append a row to CSV, and JSON as NDJSON (one JSON per line)."""
    fieldnames = [
        "path",
        "title",
        "artist",
        "album",
        "duration_ms",
        "year",
        "isrc",
        "decision",
        "score",
        "uri",
    ]
    _csv_write_header_if_empty(csv_path, fieldnames)
    # CSV
    with csv_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writerow({k: row.get(k) for k in fieldnames})
    # JSON (NDJSON)
    with json_path.open("a", encoding="utf-8") as f:
        import json

        f.write(json.dumps(row, ensure_ascii=False) + "\n")
