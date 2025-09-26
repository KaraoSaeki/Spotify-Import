from __future__ import annotations

from typing import List, Optional

from rapidfuzz import fuzz

from .types import Candidate, LocalTrack
from .utils import (
    call_spotify_with_retries,
    clamp,
    format_duration,
    normalize_str,
    remove_feat,
    strip_suffixes,
)


def _artist_join(artists: List[str]) -> str:
    return ", ".join(artists)


def _duration_component(local_ms: Optional[int], cand_ms: Optional[int]) -> float:
    if not local_ms or not cand_ms:
        return 0.0
    delta = abs(local_ms - cand_ms)
    if delta <= 3000:
        return 1.0
    # linearly decrease after 3s, zero after 30s
    return clamp(1.0 - (delta - 3000) / 27000.0, 0.0, 1.0)


def score_candidate(lt: LocalTrack, cand: Candidate) -> float:
    """Compute score in [0,1] using fuzzy title/artist/album and duration proximity.

    Weights: title 0.4, artist 0.4, album 0.1, duration 0.1
    Bonuses: year +/-1 (+0.02), tracknumber exact (+0.02) or +/-1 (+0.01)
    """
    # Normalize strings and strip noisy suffixes
    lt_title = strip_suffixes(lt.title or "")
    lt_artist = remove_feat(lt.artist or "")
    lt_album = strip_suffixes(lt.album or "")

    cand_title = strip_suffixes(cand.name)
    cand_artist = _artist_join(cand.artists)
    cand_album = strip_suffixes(cand.album)

    t_score = fuzz.token_set_ratio(lt_title, cand_title) / 100.0 if lt_title and cand_title else 0.0
    a_score = fuzz.token_set_ratio(lt_artist, cand_artist) / 100.0 if lt_artist and cand_artist else 0.0
    al_score = fuzz.token_set_ratio(lt_album, cand_album) / 100.0 if lt_album and cand_album else 0.0
    d_score = _duration_component(lt.duration_ms, cand.duration_ms)

    # Base weights
    wt_t, wt_a, wt_al, wt_d = 0.4, 0.4, 0.1, 0.1
    used = []
    if t_score > 0 or (lt_title and cand_title):
        used.append((wt_t, t_score))
    if a_score > 0 or (lt_artist and cand_artist):
        used.append((wt_a, a_score))
    if al_score > 0 and lt_album and cand_album:
        used.append((wt_al, al_score))
    if lt.duration_ms and cand.duration_ms:
        used.append((wt_d, d_score))
    total_w = sum(w for w, _ in used) or 1.0
    base = sum(w * s for w, s in used) / total_w

    bonus = 0.0
    if lt.year and cand.release_year:
        if abs(lt.year - cand.release_year) <= 1:
            bonus += 0.02
    if lt.tracknumber and cand.track_number:
        if lt.tracknumber == cand.track_number:
            bonus += 0.02
        elif abs(lt.tracknumber - cand.track_number) <= 1:
            bonus += 0.01

    return clamp(base + bonus, 0.0, 1.0)


def _cand_from_item(item) -> Candidate:
    artists = [a.get("name", "") for a in item.get("artists", [])]
    album = (item.get("album") or {}).get("name", "")
    duration_ms = int(item.get("duration_ms") or 0)
    release_date = (item.get("album") or {}).get("release_date")
    release_year = None
    if release_date:
        try:
            release_year = int(release_date[:4])
        except Exception:
            release_year = None
    track_number = item.get("track_number")
    try:
        track_number = int(track_number) if track_number is not None else None
    except Exception:
        track_number = None

    return Candidate(
        uri=item.get("uri"),
        name=item.get("name", ""),
        artists=artists,
        album=album,
        duration_ms=duration_ms,
        score=0.0,
        release_year=release_year,
        track_number=track_number,
    )


def search_candidates(sp, lt: LocalTrack, market: str, limit: int) -> List[Candidate]:
    """Search Spotify for candidates using a strategy of queries, then score locally."""
    queries: List[str] = []
    if lt.isrc:
        queries.append(f"isrc:{lt.isrc}")

    title = strip_suffixes(lt.title or "")
    artist = remove_feat(lt.artist or "")

    if title and artist:
        queries.append(f'track:"{title}" artist:"{artist}"')
        queries.append(f"{title} {artist}")
        queries.append(f"{strip_suffixes(title)} {artist}")
        queries.append(f"{remove_feat(title)} {remove_feat(artist)}")
    elif title:
        queries.append(f'track:"{title}"')
        queries.append(title)
    elif artist:
        queries.append(f'artist:"{artist}"')

    seen_ids = set()
    items = []

    for q in queries:
        resp = call_spotify_with_retries(sp.search, q=q, type="track", market=market, limit=20)
        tracks = (resp or {}).get("tracks", {})
        for it in tracks.get("items", []):
            tid = it.get("id")
            if not tid or tid in seen_ids:
                continue
            seen_ids.add(tid)
            items.append(it)
        if len(items) >= 20:
            break

    cands = [_cand_from_item(it) for it in items]
    for c in cands:
        c.score = score_candidate(lt, c)
    cands.sort(key=lambda c: c.score, reverse=True)
    return cands[: max(limit, 1)]


class _UserQuit(Exception):
    pass


def _print_candidates(cands: List[Candidate], max_to_show: int = 5) -> None:
    from rich.table import Table
    from rich.console import Console

    console = Console()
    table = Table(title="Meilleurs candidats", show_lines=False)
    table.add_column("#", justify="right")
    table.add_column("Titre — Artiste")
    table.add_column("Album")
    table.add_column("Durée")
    table.add_column("Score")
    table.add_column("URI")

    max_to_show = max(1, min(5, int(max_to_show)))
    for i, c in enumerate(cands[:max_to_show], 1):
        table.add_row(
            str(i),
            f'"{c.name}" — {", ".join(c.artists)}',
            c.album,
            format_duration(c.duration_ms),
            f"{c.score:.2f}",
            c.uri,
        )
    console.print(table)


def decide_with_auto_or_menu(
    cands: List[Candidate],
    lt: LocalTrack,
    auto_accept: float,
    dry_run: bool,
    sp=None,
    market: Optional[str] = None,
    max_candidates: int = 5,
) -> Optional[str]:
    """Return URI if accepted, else None. If dry_run, still return best URI but caller should avoid adding.

    If top candidate score >= auto_accept, auto-accept; otherwise show up to 5 and prompt.
    Choices: [1-5] select, [s]kip, [m]anual, [q]uit
    """
    max_candidates = min(max_candidates, 5)
    best = cands[0] if cands else None
    if best and best.score >= auto_accept:
        return best.uri

    # Interactive menu
    if not cands:
        return None

    _print_candidates(cands, max_to_show=max_candidates)
    while True:
        choice = input("[s]kip, [m]anual, [1-5], [q]uit > ").strip().lower()
        if choice in {"q", "quit"}:
            raise _UserQuit()
        if choice in {"s", "skip", ""}:
            return None
        if choice in {"m", "manual"}:
            if sp is None:
                print("Requête manuelle indisponible (client non fourni).")
                continue
            query = input("Saisir une requête manuelle: ").strip()
            if not query:
                continue
            resp = call_spotify_with_retries(
                sp.search, q=query, type="track", market=(market or "FR"), limit=20
            )
            items = (resp or {}).get("tracks", {}).get("items", [])
            cands = [_cand_from_item(it) for it in items]
            for c in cands:
                c.score = score_candidate(lt, c)
            cands.sort(key=lambda c: c.score, reverse=True)
            _print_candidates(cands, max_to_show=max_candidates)
            continue
        if choice.isdigit():
            idx = int(choice)
            max_to_show = max(1, min(5, int(max_candidates)))
            if 1 <= idx <= min(max_to_show, len(cands)):
                return cands[idx - 1].uri
        print("Entrée invalide. Réessayez.")
