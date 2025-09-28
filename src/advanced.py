from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Optional

# Optional HTTP dependency; imported lazily to avoid hard failure if missing

def _safe_import_requests():
    try:
        import requests  # type: ignore

        return requests
    except Exception:
        return None


def _extract_hints_from_filename(path: Path) -> Dict[str, Optional[str]]:
    """Extract naive hints from a filename like 'Bleach OP7 Raw.mp3'.

    Returns keys: base, opseq (e.g. '7'), edseq, type ('OP'|'ED'|None)
    """
    name = path.stem
    # Normalize
    s = name
    s = s.replace("_", " ")
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"(?i)\b(raw|ost|audio|rip|hq|hd|full|tv size|tv-size)\b", "", s)
    s = re.sub(r"\s+", " ", s).strip()

    # Detect OP/ED and sequence number
    type_ = None
    opseq = None
    edseq = None
    m = re.search(r"(?i)\bop\s*([0-9]+)\b", s)
    if m:
        type_ = "OP"
        opseq = m.group(1)
    m2 = re.search(r"(?i)\bed\s*([0-9]+)\b", s)
    if m2:
        type_ = "ED"
        edseq = m2.group(1)

    # Guess base anime name as the part before OP/ED token
    base = s
    base = re.split(r"(?i)\bop\b|\bed\b", base)[0].strip() or s

    return {"base": base, "type": type_, "opseq": opseq, "edseq": edseq}


def enhance_from_filename_anime(path_like) -> Optional[Dict[str, str]]:
    """Given a local file path, try to infer a better (title, artist) using anime OP/ED catalogs.

    Strategy:
    - Parse filename for base anime name and OP/ED sequence.
    - Query animethemes.moe API to find matching theme.
    - Return {"title": song_title, "artist": artist_joined} if found.

    Returns None if nothing reliable is found.
    """
    p = Path(path_like)
    hints = _extract_hints_from_filename(p)
    base = hints.get("base") or ""
    t = hints.get("type")
    opseq = hints.get("opseq")
    edseq = hints.get("edseq")

    # If we have no base at all, give up early
    if not base or len(base) < 2:
        return None

    requests = _safe_import_requests()
    if requests is None:
        return None

    # animethemes.moe API: search anime and include themes with songs and artists
    # Docs: https://api.animethemes.moe/docs
    params = {
        "search": base,
        "include": "animethemes,animethemes.song,animethemes.artists,animethemes.animethemeentries",
        "limit": 10,
    }
    try:
        resp = requests.get("https://api.animethemes.moe/anime", params=params, timeout=8)
        if resp.status_code != 200:
            return None
        data = resp.json()
    except Exception:
        return None

    def pick_theme(anime_item) -> Optional[Dict[str, str]]:
        themes = anime_item.get("animethemes") or []
        # Filter by type OP/ED if present
        if t in {"OP", "ED"}:
            themes = [th for th in themes if (th.get("type") or "").upper() == t]
        # Select by sequence number if provided
        if (t == "OP" and opseq) or (t == "ED" and edseq):
            seq = int(opseq or edseq or 0)
            # animethemes use 'sequence' as integer, may be None
            def score_theme(th) -> int:
                s = th.get("sequence")
                try:
                    s = int(s) if s is not None else 0
                except Exception:
                    s = 0
                # Higher score for exact sequence match
                return 100 if s == seq else (50 - abs(s - seq))

            if themes:
                themes.sort(key=score_theme, reverse=True)
        # Fallback: keep order
        if not themes:
            return None

        th0 = themes[0]
        song = th0.get("song") or {}
        artists = song.get("artists") or []
        artist_names = ", ".join([a.get("name", "") for a in artists if a.get("name")])
        title = song.get("title") or song.get("name") or ""
        if title:
            return {"title": title, "artist": artist_names}
        return None

    items = (data or {}).get("anime") or []
    # Basic heuristic: prefer items whose name contains the base (case-insensitive)
    def item_score(it) -> int:
        name = (it.get("name") or "") + " " + (it.get("slug") or "")
        name = name.lower()
        b = base.lower()
        sc = 0
        if b in name:
            sc += 10
        # small bonus if season 1 or default
        sc += 1
        return sc

    items.sort(key=item_score, reverse=True)
    for it in items:
        picked = pick_theme(it)
        if picked:
            return picked

    return None
