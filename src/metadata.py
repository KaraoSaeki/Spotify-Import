from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from .types import LocalTrack
from .utils import remove_feat, strip_suffixes, safe_int


def _extract_isrc_generic(tags) -> Optional[str]:
    if not tags:
        return None
    # Try common keys across formats
    for key in ("isrc", "TSRC", "TXXX:ISRC", "itunesisrc", "ISRC"):
        v = tags.get(key)
        if not v:
            continue
        if isinstance(v, (list, tuple)):
            v = v[0]
        try:
            s = str(v)
        except Exception:
            continue
        s = s.strip()
        if s:
            return s
    return None


def read_tags(path: Path) -> LocalTrack:
    """Read tags via mutagen and return LocalTrack skeleton.

    Tries easy tags first; extracts title, artist, album, tracknumber, year/date,
    duration_ms and ISRC if available.
    """
    # Lazy import mutagen to keep this module importable without the package
    try:
        from mutagen import File as MutagenFile  # type: ignore
        from mutagen.id3 import ID3, TSRC  # type: ignore
    except Exception:  # pragma: no cover
        MutagenFile = None  # type: ignore
        ID3 = None  # type: ignore
        TSRC = None  # type: ignore

    audio = MutagenFile(path) if MutagenFile else None
    title = artist = album = None
    duration_ms = None
    year = None
    isrc = None
    tracknum = None

    if audio is not None:
        # duration
        try:
            if getattr(audio, "info", None) and getattr(audio.info, "length", None):
                duration_ms = int(audio.info.length * 1000)
        except Exception:
            pass

        tags = getattr(audio, "tags", None)
        # Try easy-like and multiple tag formats
        try:
            title = (
                (tags.get("title")[0] if isinstance(tags.get("title"), list) else tags.get("title"))
                if tags and tags.get("title")
                else None
            )
        except Exception:
            pass
        try:
            # Try multiple artist tag formats (artist, TPE1, ©ART, etc.)
            artist = None
            for key in ("artist", "TPE1", "©ART", "ARTIST"):
                if tags and tags.get(key):
                    val = tags.get(key)
                    artist = val[0] if isinstance(val, list) else val
                    # Convert to string if it's a tag object
                    if artist:
                        artist = str(artist) if not isinstance(artist, str) else artist
                        break
        except Exception:
            pass
        try:
            album = (
                (tags.get("album")[0] if isinstance(tags.get("album"), list) else tags.get("album"))
                if tags and tags.get("album")
                else None
            )
        except Exception:
            pass
        try:
            tn = (
                (tags.get("tracknumber")[0] if isinstance(tags.get("tracknumber"), list) else tags.get("tracknumber"))
                if tags and tags.get("tracknumber")
                else None
            )
            tracknum = safe_int(tn)
        except Exception:
            pass
        # Year/date
        try:
            y = None
            for k in ("date", "year"):  # many formats
                v = tags.get(k) if tags else None
                if v:
                    if isinstance(v, list):
                        v = v[0]
                    y = str(v)
                    break
            if y:
                y = re.findall(r"(\d{4})", y)
                if y:
                    year = int(y[0])
        except Exception:
            pass

        # ISRC generic
        try:
            isrc = _extract_isrc_generic(tags)
        except Exception:
            pass

        # Specific ID3 TSRC frame for MP3
        if isrc is None and ID3 and TSRC:
            try:
                id3 = ID3(path)
                frame = id3.get("TSRC")
                if frame and isinstance(frame, TSRC):
                    isrc = str(frame.text[0]) if frame.text else None
            except Exception:
                pass

    return LocalTrack(
        path=path,
        title=title.strip() if isinstance(title, str) else title,
        artist=artist.strip() if isinstance(artist, str) else artist,
        album=album.strip() if isinstance(album, str) else album,
        duration_ms=duration_ms,
        year=year,
        isrc=isrc,
        tracknumber=tracknum,
    )


_artist_title_sep = re.compile(r"\s*-\s*|\s*_\s*")


def infer_from_filename(path: Path, lt: LocalTrack) -> LocalTrack:
    """Fallback: parse common patterns from filename to fill missing title/artist.

    Supports patterns like:
    - Artist - Title.ext
    - Artist_Title.ext
    Removes noisy suffixes like (Remastered), [Radio Edit] and feat.
    """
    stem = path.stem
    # remove suffixes, but do not discard every bracket content; strip_suffixes removes common keywords
    cleaned = strip_suffixes(stem)

    if lt.title and lt.artist:
        # Already present, still normalize title by stripping suffixes
        return LocalTrack(
            path=lt.path,
            title=strip_suffixes(lt.title),
            artist=lt.artist,
            album=lt.album,
            duration_ms=lt.duration_ms,
            year=lt.year,
            isrc=lt.isrc,
            tracknumber=lt.tracknumber,
        )

    parts = _artist_title_sep.split(cleaned)
    if len(parts) >= 2:
        artist = parts[0].strip()
        title = "-".join(parts[1:]).strip()
        artist = remove_feat(artist)
        title = remove_feat(strip_suffixes(title))
        return LocalTrack(
            path=lt.path,
            title=lt.title or title,
            artist=lt.artist or artist,
            album=lt.album,
            duration_ms=lt.duration_ms,
            year=lt.year,
            isrc=lt.isrc,
            tracknumber=lt.tracknumber,
        )

    # If unable to split, fall back to stem as title
    title = remove_feat(strip_suffixes(cleaned))
    return LocalTrack(
        path=lt.path,
        title=lt.title or title,
        artist=lt.artist,
        album=lt.album,
        duration_ms=lt.duration_ms,
        year=lt.year,
        isrc=lt.isrc,
        tracknumber=lt.tracknumber,
    )
