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
    
    # Remove track numbers at the beginning (e.g., "14. Title" -> "Title")
    s = re.sub(r"^\d+\.\s*", "", s)
    
    # Extract OP/ED info from Japanese brackets before removing them
    # e.g., 【New Opening 24】 -> detect OP24
    type_ = None
    opseq = None
    edseq = None
    
    bracket_match = re.search(r"【[^】]*(?:opening|op)\s*(\d+)[^】]*】", s, re.IGNORECASE)
    if bracket_match:
        type_ = "OP"
        opseq = bracket_match.group(1)
    else:
        bracket_match = re.search(r"【[^】]*(?:ending|ed)\s*(\d+)[^】]*】", s, re.IGNORECASE)
        if bracket_match:
            type_ = "ED"
            edseq = bracket_match.group(1)
    
    # Remove Japanese/Chinese brackets and their content (【MAD】, 【New Opening 24】)
    s = re.sub(r"【[^】]*】", "", s)
    
    # Remove square brackets content that looks like metadata [AMV], [MAD], etc.
    s = re.sub(r"\[(AMV|MAD|MMV|PMV|HD|HQ|1080p|720p|480p)\]", "", s, flags=re.IGNORECASE)
    
    s = re.sub(r"\s+", " ", s).strip()
    # Remove common noise patterns including NC (Non-Credit)
    s = re.sub(r"(?i)\b(raw|ost|audio|rip|hq|hd|full|tv size|tv-size|nc|non-credit|creditless|mad|amv|mmv|pmv)\b", "", s)
    s = re.sub(r"\s+", " ", s).strip()

    # Detect OP/ED and sequence number from main text (if not found in brackets)
    base = s
    
    # Only search in main text if not already found in brackets
    if not type_:
        # Match OP14, OP 14, Opening14, Opening 14, etc.
        m = re.search(r"(?i)\b(?:op|opening)\s*([0-9]+)\b", s)
        if m:
            type_ = "OP"
            opseq = m.group(1)
            # Extract base as everything before the match
            base = s[:m.start()].strip()
        else:
            # Match ED14, ED 14, Ending14, Ending 14, etc.
            m2 = re.search(r"(?i)\b(?:ed|ending)\s*([0-9]+)\b", s)
            if m2:
                type_ = "ED"
                edseq = m2.group(1)
                # Extract base as everything before the match
                base = s[:m2.start()].strip()
    
    # If no OP/ED found, base remains the full string
    if not base or (type_ and not base):
        base = s

    return {"base": base, "type": type_, "opseq": opseq, "edseq": edseq}


def _try_romanize_title(title: str) -> Optional[str]:
    """Try to romanize Japanese/Chinese title using common patterns.
    
    This is a simple heuristic - for better results, would need a proper
    transliteration library like 'pykakasi' or 'romkan'.
    """
    # For now, just return None - the multi-market search should handle it
    # Future: could use pykakasi or similar for Japanese romanization
    return None


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
    # Try exact filter first, then fallback to search with variations
    # Common variations: "Naruto Shippuden" -> "Naruto: Shippuuden", etc.
    base_variations = [base]
    
    # Add variations for common anime name patterns
    if "shippuden" in base.lower():
        base_variations.append(base.replace("Shippuden", "Shippuuden"))
        base_variations.append(base.replace("Shippuden", "Shippuden"))
        # Try with colon
        base_variations.append(base.replace(" Shippuden", ": Shippuuden"))
        base_variations.append(base.replace(" Shippuden", ": Shippuden"))
    
    params_list = []
    for variant in base_variations:
        params_list.append({
            "filter[name]": variant,
            "include": "animethemes.song.artists",
            "limit": 3,
        })
    
    # Add like searches as fallback
    for variant in base_variations[:2]:  # Only first 2 to avoid too many requests
        params_list.append({
            "filter[name]-like": f"%{variant}%",
            "include": "animethemes.song.artists",
            "limit": 5,
        })
    
    data = None
    for params in params_list:
        try:
            resp = requests.get("https://api.animethemes.moe/anime", params=params, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("anime"):
                    break
        except Exception:
            continue
    
    if not data or not data.get("anime"):
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
        # Fallback: if no themes match, try without type filter
        if not themes:
            themes = anime_item.get("animethemes") or []
            if not themes:
                return None

        th0 = themes[0]
        song = th0.get("song") or {}
        artists = song.get("artists") or []
        
        # If artists are not included, try fetching the theme directly
        if not artists and th0.get("id"):
            try:
                theme_resp = requests.get(
                    f"https://api.animethemes.moe/animetheme/{th0['id']}",
                    params={"include": "song.artists"},
                    timeout=5
                )
                if theme_resp.status_code == 200:
                    theme_data = theme_resp.json().get("animetheme", {})
                    song = theme_data.get("song") or song
                    artists = song.get("artists") or []
            except Exception:
                pass
        
        artist_names = ", ".join([a.get("name", "") for a in artists if a.get("name")])
        title = song.get("title") or song.get("name") or ""
        if title:
            return {"title": title, "artist": artist_names}
        return None

    items = data.get("anime") or []
    # Basic heuristic: prefer exact matches, then items whose name contains the base
    def item_score(it) -> int:
        name = (it.get("name") or "")
        slug = (it.get("slug") or "")
        name_lower = name.lower()
        slug_lower = slug.lower()
        b = base.lower()
        sc = 0
        # Exact match gets highest score
        if name_lower == b or slug_lower == b:
            sc += 100
        # Contains match
        elif b in name_lower or b in slug_lower:
            sc += 50
        # Partial word match
        elif any(word in name_lower or word in slug_lower for word in b.split()):
            sc += 10
        return sc

    items.sort(key=item_score, reverse=True)
    for it in items:
        picked = pick_theme(it)
        if picked:
            return picked

    return None
