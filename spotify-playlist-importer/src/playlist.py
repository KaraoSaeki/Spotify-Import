from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Iterable, List, Optional, Set

from rich.console import Console
from rich.table import Table

from .types import PlaylistInfo
from .utils import brief_id, chunked

console = Console()


def ensure_playlist_create(
    sp,
    name: str,
    public: bool,
    collaborative: bool,
    description: Optional[str] | None,
) -> PlaylistInfo:
    me = sp.me()
    user_id = me["id"]
    payload = {
        "name": name,
        "public": public,
        "collaborative": collaborative,
        "description": description or "",
    }
    pl = sp.user_playlist_create(user=user_id, **payload)
    owner = pl.get("owner", {})
    return PlaylistInfo(
        id=pl["id"],
        name=pl["name"],
        owner_id=owner.get("id", ""),
        owner_name=owner.get("display_name") or owner.get("id", ""),
        public=bool(pl.get("public")),
        collaborative=bool(pl.get("collaborative")),
        tracks_total=(pl.get("tracks") or {}).get("total", 0),
    )


def list_user_playlists(sp, page_size: int = 50) -> List[PlaylistInfo]:
    items: List[PlaylistInfo] = []
    offset = 0
    while True:
        resp = sp.current_user_playlists(limit=page_size, offset=offset)
        for it in resp.get("items", []):
            owner = it.get("owner", {})
            items.append(
                PlaylistInfo(
                    id=it["id"],
                    name=it["name"],
                    owner_id=owner.get("id", ""),
                    owner_name=owner.get("display_name") or owner.get("id", ""),
                    public=bool(it.get("public")),
                    collaborative=bool(it.get("collaborative")),
                    tracks_total=(it.get("tracks") or {}).get("total", 0),
                )
            )
        if resp.get("next"):
            offset += page_size
        else:
            break
    return items


def safe_select_playlist_interactive(playlists: List[PlaylistInfo]) -> Optional[PlaylistInfo]:
    filtered = playlists
    page = 0
    page_size = 10

    while True:
        filt = input("Filtre (laisser vide pour tout) : ").strip().lower()
        if filt:
            filtered = [p for p in playlists if filt in p.name.lower()]
        else:
            filtered = playlists
        if not filtered:
            print("Aucune playlist.")
            return None
        break

    while True:
        total_pages = (len(filtered) + page_size - 1) // page_size
        start = page * page_size
        page_items = filtered[start : start + page_size]

        table = Table(title=f"Page {page+1}/{max(total_pages,1)}")
        table.add_column("#", justify="right")
        table.add_column("Nom")
        table.add_column("Propriétaire")
        table.add_column("Tracks")
        table.add_column("Public/Privé")
        table.add_column("Collab")
        table.add_column("ID")

        for idx, p in enumerate(page_items, start=1):
            table.add_row(
                str(idx),
                p.name,
                p.owner_name,
                str(p.tracks_total),
                "Public" if p.public else "Privé",
                "Oui" if p.collaborative else "Non",
                brief_id(p.id),
            )
        console.print(table)

        choice = input("[n] suivante, [p] précédente, [#] sélectionner, [q] quitter\n> ").strip().lower()
        if choice == "n" and page + 1 < total_pages:
            page += 1
            continue
        if choice == "p" and page > 0:
            page -= 1
            continue
        if choice == "q":
            return None
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(page_items):
                selection = page_items[idx - 1]
                print(
                    f'Vous avez choisi: "{selection.name}" ({selection.tracks_total} titres) — propriétaire: {selection.owner_name}'
                )
                conf1 = input(f"Confirmez en retapant l'index ({idx}) puis Y/N :\n> ").strip()
                conf2 = input(
                    "Y/N ? ".strip()
                ).strip().lower()
                if conf1 == str(idx) and conf2 == "y":
                    return selection
                else:
                    print("Annulé.")
        print("Entrée invalide.")


def ensure_rights_or_fail(sp, pl: PlaylistInfo) -> None:
    me = sp.me()
    if pl.owner_id != me["id"] and not pl.collaborative:
        raise PermissionError(
            "Vous n'êtes pas propriétaire de cette playlist et elle n'est pas collaborative."
        )


def get_playlist_track_uris(sp, playlist_id: str) -> Set[str]:
    uris: Set[str] = set()
    limit = 100
    offset = 0
    while True:
        try:
            resp = sp.playlist_items(playlist_id, fields=None, limit=limit, offset=offset)
        except Exception as e:
            status = getattr(e, "http_status", None)
            if status == 429:
                ra = int(getattr(e, "headers", {}).get("Retry-After", 1))
                time.sleep(ra + 1)
                continue
            else:
                raise
        items = resp.get("items", [])
        for it in items:
            track = it.get("track") or {}
            uri = track.get("uri")
            if uri:
                uris.add(uri)
        if resp.get("next"):
            offset += limit
        else:
            break
    return uris


def add_tracks_batched(sp, playlist_id: str, uris: List[str]) -> None:
    for batch in chunked(uris, 100):
        while True:
            try:
                sp.playlist_add_items(playlist_id, batch)
                break
            except Exception as e:
                status = getattr(e, "http_status", None)
                if status == 429:
                    ra = int(getattr(e, "headers", {}).get("Retry-After", 1))
                    time.sleep(ra + 1)
                    continue
                else:
                    raise
