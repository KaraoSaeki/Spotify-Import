from __future__ import annotations

import csv
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Iterable, Iterator, List, Sequence, Tuple, TypeVar

from tenacity import retry, stop_after_attempt, wait_random_exponential

T = TypeVar("T")


DEFAULT_EXTS = [
    "mp3",
    "m4a",
    "aac",
    "flac",
    "ogg",
    "opus",
    "wav",
    "aiff",
    "alac",
    "wma",
    "aif",
]


def now_timestamp_str() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def chunked(seq: Sequence[T] | Iterable[T], n: int) -> Iterator[List[T]]:
    """Yield lists of size n from a sequence/iterable."""
    if n <= 0:
        raise ValueError("n must be > 0")
    buf: List[T] = []
    for item in seq:
        buf.append(item)
        if len(buf) >= n:
            yield buf
            buf = []
    if buf:
        yield buf


def format_duration(ms: int | None) -> str:
    if not ms or ms <= 0:
        return "--:--"
    s = ms // 1000
    m, s = divmod(s, 60)
    return f"{int(m):02d}:{int(s):02d}"


_feat_re = re.compile(r"\b(feat\.|ft\.)\b.*", re.IGNORECASE)
_paren_re = re.compile(r"\s*[\[(][^\])]*(remaster|live|edit|version|mono|stereo|deluxe|explicit)[^\])]*[\])]", re.IGNORECASE)
_brackets_re = re.compile(r"\s*[\[(].*?[\])]", re.IGNORECASE)
_ws_re = re.compile(r"\s+")


def strip_suffixes(text: str) -> str:
    """Remove common suffixes like (Live), (Remastered 2011), [Radio Edit]."""
    if not text:
        return text
    t = _paren_re.sub("", text)
    t = _brackets_re.sub("", t)
    return _ws_re.sub(" ", t).strip()


def remove_feat(text: str) -> str:
    if not text:
        return text
    return _feat_re.sub("", text).strip()


def normalize_str(s: str | None) -> str:
    return (s or "").strip().lower()


def safe_int(value: str | int | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except Exception:
        try:
            return int(str(value).split("/")[0])
        except Exception:
            return None


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def brief_id(s: str, prefix: int = 3, suffix: int = 2) -> str:
    if len(s) <= prefix + suffix + 3:
        return s
    return f"{s[:prefix]}...{s[-suffix:]}"


def _is_rate_limited_exception(e: Exception) -> bool:
    return getattr(e, "http_status", None) == 429


def _retry_after_seconds(e: Exception) -> int:
    try:
        headers = getattr(e, "headers", {}) or {}
        ra = int(headers.get("Retry-After", 1))
        return max(1, ra)
    except Exception:
        return 1


@retry(reraise=True, stop=stop_after_attempt(6), wait=wait_random_exponential(multiplier=1, max=10))
def call_spotify_with_retries(func, *args, **kwargs):
    """Call a Spotify client method with retry/backoff and 429 handling.

    If a 429 occurs and Retry-After header is present, sleep that duration then retry.
    Uses exponential backoff with jitter for other transient exceptions.
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if _is_rate_limited_exception(e):
            time.sleep(_retry_after_seconds(e) + 1)
        raise
