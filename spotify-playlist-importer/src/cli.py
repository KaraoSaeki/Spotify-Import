from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional, Set

from rich.console import Console
from tqdm import tqdm

from .auth import get_spotify_client
from .log_utils import init_summaries, setup_logging, write_summary_row
from .matcher import _UserQuit, decide_with_auto_or_menu, search_candidates, score_candidate
from .metadata import infer_from_filename, read_tags
from .playlist import (
    add_tracks_batched,
    ensure_playlist_create,
    ensure_rights_or_fail,
    get_playlist_track_uris,
    list_user_playlists,
    safe_select_playlist_interactive,
)
from .types import ADDED, AMBIGUOUS, DUPLICATE, NOT_FOUND, PLANNED_ADD, LocalTrack
from .utils import DEFAULT_EXTS
from .utils import strip_suffixes, remove_feat
from .scanner import iter_audio_files

console = Console()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="spotify-playlist-importer",
        description="Importer des fichiers audio locaux vers une playlist Spotify (matching)",
    )
    p.add_argument("--path-import", required=True, help="Chemin du dossier à scanner")
    p.add_argument("--market", default="FR")
    p.add_argument("--public", action="store_true")
    p.add_argument("--private", action="store_true")
    p.add_argument("--collab", action="store_true")
    p.add_argument("--auto-accept", type=float, default=0.92)
    p.add_argument("--max-candidates", type=int, default=5)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--resume", type=str, default=None, help="Chemin vers state.json")
    p.add_argument(
        "--extensions",
        type=str,
        default=",".join(DEFAULT_EXTS),
        help="Liste CSV d'extensions",
    )
    p.add_argument("--no-follow-symlinks", action="store_true")
    p.add_argument("--ignore-hidden", action="store_true")
    return p.parse_args()


def prompt_main_menu() -> str:
    console.print("Que souhaitez-vous faire ?")
    console.print("[1] Créer une nouvelle playlist")
    console.print("[2] Mettre à jour une playlist existante")
    console.print("[Q] Quitter")
    while True:
        c = input("> ").strip().lower()
        if c == "1":
            return "create"
        if c == "2":
            return "update"
        if c in {"q", "quit"}:
            return "quit"
        print("Entrée invalide.")


def prompt_new_playlist_meta(args) -> dict:
    name = ""
    while not name:
        name = input("Nom de la playlist (obligatoire): ").strip()
    # Defaults from CLI flags
    public = True if args.public and not args.private else False if args.private else False
    collab = bool(args.collab)
    ans_pub = input(f"Playlist publique ? (Y/N) [defaut={'Y' if public else 'N'}]: ").strip().lower()
    if ans_pub in {"y", "n"}:
        public = ans_pub == "y"
    ans_col = input(f"Collaborative ? (Y/N) [defaut={'Y' if collab else 'N'}]: ").strip().lower()
    if ans_col in {"y", "n"}:
        collab = ans_col == "y"
    description = input("Description (optionnel): ").strip() or None
    return {"name": name, "public": public, "collaborative": collab, "description": description}


def decide_status(best_uri: Optional[str], existing: Set[str], dry_run: bool) -> str:
    if not best_uri:
        return NOT_FOUND
    if best_uri in existing:
        return DUPLICATE
    return PLANNED_ADD if dry_run else ADDED


def log_and_append_summary(csv_path: Path, json_path: Path, path: Path, lt: LocalTrack, best_uri: Optional[str], status: str, score: Optional[float]) -> None:
    row = {
        "path": str(path),
        "title": lt.title,
        "artist": lt.artist,
        "album": lt.album,
        "duration_ms": lt.duration_ms,
        "year": lt.year,
        "isrc": lt.isrc,
        "decision": status,
        "score": score,
        "uri": best_uri,
    }
    write_summary_row(csv_path, json_path, row)


def _load_resume(resume_path: Optional[str]) -> Dict[str, dict]:
    if not resume_path:
        return {"processed": {}}
    p = Path(resume_path)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {"processed": {}}
    return {"processed": {}}


def _save_resume(resume_path: Optional[str], state: Dict[str, dict]) -> None:
    if not resume_path:
        return
    p = Path(resume_path)
    p.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    args = parse_args()
    exts = [e.strip().lstrip(".") for e in args.extensions.split(",") if e.strip()]
    follow_symlinks = not args.no_follow_symlinks

    logger, log_path = setup_logging()
    csv_path, json_path = init_summaries()

    console.print("Connexion à Spotify → navigateur ouvert…")
    sp = get_spotify_client(
        scopes=["playlist-read-private", "playlist-modify-private", "playlist-modify-public"]
    )
    me = sp.me()
    console.print(f"✔ Connecté en tant que {me.get('display_name') or me.get('id')}")

    action = prompt_main_menu()

    if action == "create":
        meta = prompt_new_playlist_meta(args)  # name/public/collab/desc
        pl = ensure_playlist_create(sp, **meta)
    elif action == "update":
        pls = list_user_playlists(sp)
        pl = safe_select_playlist_interactive(pls)
        if not pl:
            return
        ensure_rights_or_fail(sp, pl)
    else:
        return

    existing = get_playlist_track_uris(sp, pl.id)
    to_add_batch: List[str] = []

    state = _load_resume(args.resume)
    processed = set(state.get("processed", {}).keys())

    files = list(
        iter_audio_files(
            Path(args.path_import), exts=exts, follow_symlinks=follow_symlinks, ignore_hidden=args.ignore_hidden
        )
    )
    console.print(f"Scan des fichiers…  {len(files)} trouvés")
    if args.dry_run:
        console.print("[bold yellow]Mode DRY-RUN: aucun ajout ne sera effectué[/bold yellow]")

    added = skipped = not_found = ambiguous = duplicates = 0
    # Simple in-run cache: normalized (title, artist) -> list[Candidate] without relying on previous scores
    search_cache: dict[tuple[str, str], list] = {}

    try:
        for path in tqdm(files, desc="Analyse"):
            if str(path) in processed:
                continue

            lt = read_tags(path)
            lt = infer_from_filename(path, lt)

            # Build cache key on normalized title/artist
            key = (strip_suffixes(lt.title or "").lower().strip(), remove_feat(lt.artist or "").lower().strip())
            if key in search_cache:
                cands = search_cache[key]
                # Re-score for this local track context
                for c in cands:
                    c.score = score_candidate(lt, c)
                cands = sorted(cands, key=lambda c: c.score, reverse=True)
            else:
                cands = search_candidates(sp, lt, args.market, limit=20)
                search_cache[key] = cands[:]
            best_uri = None
            best_score = None
            if cands:
                best_uri = cands[0].uri
                best_score = cands[0].score
            # If under auto-accept, show interactive
            try:
                best_uri = decide_with_auto_or_menu(
                    cands,
                    lt,
                    float(args.auto_accept),
                    args.dry_run,
                    sp=sp,
                    market=args.market,
                    max_candidates=max(1, min(5, int(args.max_candidates))),
                )
                if best_uri and cands:
                    for c in cands:
                        if c.uri == best_uri:
                            best_score = c.score
                            break
            except _UserQuit:
                logger.info("Arrêt demandé par l'utilisateur. Sauvegarde de l'état.")
                state.setdefault("processed", {})[str(path)] = {"uri": best_uri, "score": best_score}
                _save_resume(args.resume, state)
                return

            status = decide_status(best_uri, existing, args.dry_run)
            if status == ADDED or status == PLANNED_ADD:
                to_add_batch.append(best_uri)  # type: ignore
                existing.add(best_uri)  # type: ignore
                added += 1
                if len(to_add_batch) >= 100 and not args.dry_run:
                    console.print("Ajout des 100 premiers titres…")
                    add_tracks_batched(sp, pl.id, to_add_batch)
                    to_add_batch.clear()
            elif status == DUPLICATE:
                duplicates += 1
            elif status == NOT_FOUND:
                not_found += 1
            else:
                skipped += 1

            log_and_append_summary(csv_path, json_path, path, lt, best_uri, status, best_score)

            state.setdefault("processed", {})[str(path)] = {"uri": best_uri, "score": best_score}
            _save_resume(args.resume, state)

        if to_add_batch and not args.dry_run:
            add_tracks_batched(sp, pl.id, to_add_batch)
            to_add_batch.clear()
    finally:
        # Print final totals
        console.print("\nRésumé:")
        console.print(
            f" ADDED={added}  SKIPPED={skipped}  NOT_FOUND={not_found}  AMBIGUOUS={ambiguous}  DUPLICATE={duplicates}"
        )
        console.print(f"Log: {log_path}")
        console.print(f"CSV: {csv_path}")
        console.print(f"JSON: {json_path}")


if __name__ == "__main__":
    main()
