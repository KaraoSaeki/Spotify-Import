from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List


@dataclass
class LocalTrack:
    """Local audio track metadata extracted from tags and/or filename."""
    path: Path
    title: Optional[str]
    artist: Optional[str]
    album: Optional[str]
    duration_ms: Optional[int]
    year: Optional[int]
    isrc: Optional[str]
    tracknumber: Optional[int] = None


@dataclass
class Candidate:
    uri: str
    name: str
    artists: List[str]
    album: str
    duration_ms: int
    score: float
    release_year: Optional[int] = None
    track_number: Optional[int] = None


@dataclass
class PlaylistInfo:
    id: str
    name: str
    owner_id: str
    owner_name: str
    public: bool
    collaborative: bool
    tracks_total: int


# Summary status constants
ADDED = "ADDED"
SKIPPED = "SKIPPED"
NOT_FOUND = "NOT_FOUND"
AMBIGUOUS = "AMBIGUOUS"
DUPLICATE = "DUPLICATE"
PLANNED_ADD = "PLANNED_ADD"  # dry-run accepted
