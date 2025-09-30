from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional, Set, IO

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
from .advanced import enhance_from_filename_anime

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
    p.add_argument("--auto-accept", type=float, default=0.92, help="Score minimum pour auto-accepter (défaut: 0.92)")
    p.add_argument("--auto-deny", type=float, default=None, help="Score maximum pour auto-refuser (ex: 0.5 refuse tout score <= 0.5)")
    p.add_argument("--max-candidates", type=int, default=5)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--resume", type=str, default=None, help="Chemin vers state.json")
    p.add_argument("--exclude", type=str, default=None, help="Mots-clés à exclure (séparés par des virgules, ex: 'AMV,RIRE JAUNE')")
    p.add_argument(
        "--extensions",
        type=str,
        default=",".join(DEFAULT_EXTS),
        help="Liste CSV d'extensions",
    )
    p.add_argument("--no-follow-symlinks", action="store_true")
    p.add_argument("--ignore-hidden", action="store_true")
    p.add_argument("--no-recursive", action="store_true", help="Ne pas descendre dans les sous-dossiers du dossier fourni")
    p.add_argument(
        "--advanced-search",
        type=str,
        choices=["anime"],
        default=None,
        help="Active une recherche avancée en fonction du nom de fichier (ex: 'anime')",
    )
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
    # Règle Spotify: une playlist collaborative ne peut pas être publique
    if collab and public:
        console.print("[yellow]Une playlist collaborative ne peut pas être publique. Passage en privée.[/yellow]")
        public = False
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
            # Fallback: try NDJSON (e.g., summary-*.json) and build a processed map from 'path' lines
            try:
                processed: Dict[str, dict] = {}
                with p.open("r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            obj = json.loads(line)
                        except Exception:
                            continue
                        path = obj.get("path")
                        if path:
                            processed[str(path)] = {"uri": obj.get("uri"), "score": obj.get("score")}
                if processed:
                    return {"processed": processed}
            except Exception:
                pass
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

    # Create per-status list files for this run
    ts = csv_path.stem.replace("summary-", "")
    reports_dir = csv_path.parent
    status_names = ["ADDED", "SKIPPED", "NOT_FOUND", "AMBIGUOUS", "DUPLICATE", "PLANNED_ADD"]
    status_fhs: dict[str, IO[str]] = {}
    try:
        for name in status_names:
            p = reports_dir / f"{name}-{ts}.txt"
            status_fhs[name] = p.open("a", encoding="utf-8")
    except Exception:
        status_fhs = {}

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
        console.print(
            f"Créée: '{pl.name}' — Public={'Oui' if pl.public else 'Non'} • Collaborative={'Oui' if pl.collaborative else 'Non'}"
        )
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

    # Load resume state and build a normalized processed set (case-insensitive, resolved paths)
    def _norm_key(p: Path | str) -> str:
        try:
            pp = Path(p).resolve(strict=False)
        except Exception:
            pp = Path(str(p))
        # Normalize to lowercase for Windows case-insensitivity and use as_posix for slashes
        return pp.as_posix().casefold()

    state = _load_resume(args.resume)
    processed_norm = { _norm_key(k) for k in state.get("processed", {}).keys() }

    files = list(
        iter_audio_files(
            Path(args.path_import), exts=exts, follow_symlinks=follow_symlinks, ignore_hidden=args.ignore_hidden, recursive=not args.no_recursive
        )
    )
    
    # Filter files based on --exclude parameter
    if args.exclude:
        exclude_keywords = [kw.strip().lower() for kw in args.exclude.split(',') if kw.strip()]
        if exclude_keywords:
            original_count = len(files)
            files = [
                f for f in files
                if not any(keyword in f.name.lower() for keyword in exclude_keywords)
            ]
            excluded_count = original_count - len(files)
            if excluded_count:
                console.print(f"[yellow]Exclusion: {excluded_count} fichiers ignorés (mots-clés: {', '.join(exclude_keywords)})[/yellow]")
    
    console.print(f"Scan des fichiers…  {len(files)} trouvés")
    # If resuming, show how many will be skipped
    try:
        skipped_already = sum(1 for f in files if _norm_key(f) in processed_norm)
        if skipped_already:
            console.print(f"Reprise: {skipped_already} déjà traités seront ignorés")
    except Exception:
        pass
    if args.dry_run:
        console.print("[bold yellow]Mode DRY-RUN: aucun ajout ne sera effectué[/bold yellow]")

    added = skipped = not_found = ambiguous = duplicates = 0
    # Simple in-run cache: normalized (title, artist) -> list[Candidate] without relying on previous scores
    search_cache: dict[tuple[str, str], list] = {}

    try:
        for path in tqdm(files, desc="Analyse"):
            key_cur = _norm_key(path)
            if key_cur in processed_norm:
                continue

            lt = read_tags(path)
            lt = infer_from_filename(path, lt)

            # Try advanced anime search FIRST if enabled (before normal search)
            anime_enhanced = False
            if args.advanced_search == "anime":
                try:
                    improved = enhance_from_filename_anime(path)
                    if improved and (improved.get("title") or improved.get("artist")):
                        logger.info(f"Anime metadata found: {improved.get('title')} by {improved.get('artist')}")
                        # Build a transient LocalTrack-like context with improved metadata
                        lt = LocalTrack(
                            path=lt.path,
                            title=improved.get("title") or lt.title,
                            artist=improved.get("artist") or lt.artist,
                            album=lt.album,
                            duration_ms=lt.duration_ms,
                            year=lt.year,
                            isrc=lt.isrc,
                            tracknumber=lt.tracknumber,
                        )
                        anime_enhanced = True
                except Exception as e:
                    logger.debug(f"Anime search failed: {e}")

            # Build cache key on normalized title/artist
            key = (strip_suffixes(lt.title or "").lower().strip(), remove_feat(lt.artist or "").lower().strip())
            if key in search_cache and not anime_enhanced:
                # Use cache only if we didn't enhance with anime data
                cands = search_cache[key]
                # Re-score for this local track context
                for c in cands:
                    c.score = score_candidate(lt, c)
                cands = sorted(cands, key=lambda c: c.score, reverse=True)
            else:
                cands = search_candidates(sp, lt, args.market, limit=20)
                if not anime_enhanced:
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
                    local_path=str(path),
                    auto_deny=float(args.auto_deny) if args.auto_deny is not None else None,
                )
                if best_uri and cands:
                    for c in cands:
                        if c.uri == best_uri:
                            best_score = c.score
                            break
            except _UserQuit:
                logger.info("Arrêt demandé par l'utilisateur. Sauvegarde de l'état.")
                state.setdefault("processed", {})[key_cur] = {"uri": best_uri, "score": best_score}
                _save_resume(args.resume, state)
                return

            status = decide_status(best_uri, existing, args.dry_run)
            # Append path to per-status list file (once)
            try:
                if status in status_fhs:
                    status_fhs[status].write(str(path) + "\n")
            except Exception:
                pass

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

            state.setdefault("processed", {})[key_cur] = {"uri": best_uri, "score": best_score}
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
        # Close any open status files
        try:
            for fh in status_fhs.values():
                try:
                    fh.close()
                except Exception:
                    pass
        except Exception:
            pass


if __name__ == "__main__":
    main()
