from __future__ import annotations

import os
from pathlib import Path
from typing import Generator, Iterable, Iterator, List, Sequence


def _is_hidden(path: Path) -> bool:
    name = path.name
    if name.startswith("."):
        return True
    # On Windows, hidden attribute isn't trivial to read without ctypes; best-effort via dotfiles.
    return False


def iter_audio_files(
    root: Path | str,
    exts: Sequence[str],
    follow_symlinks: bool,
    ignore_hidden: bool,
    recursive: bool = True,
    exclude_dirs: Sequence[str] = None,
) -> Iterator[Path]:
    """Yield Path des fichiers audio valides.

    - root: dossier racine
    - exts: extensions autorisées, sans point (ex: ["mp3", "flac"]).
    - recursive: si False, ne pas descendre dans les sous-dossiers.
    - exclude_dirs: noms de dossiers à exclure (ex: ["AMV", "Covers"]).
    """
    root_path = Path(root)
    allowed = {e.lower().lstrip(".") for e in exts}
    excluded_dirs = {d.lower() for d in (exclude_dirs or [])}

    if not recursive:
        dpath = root_path
        if ignore_hidden and _is_hidden(dpath):
            return
        # Parcours uniquement des fichiers du dossier racine, sans descendre
        for p in dpath.iterdir():
            if p.is_dir():
                continue
            if not follow_symlinks and p.is_symlink():
                continue
            if ignore_hidden and _is_hidden(p):
                continue
            ext = p.suffix.lower().lstrip(".")
            if ext in allowed:
                yield p
        return

    for dirpath, dirnames, filenames in os.walk(root_path, followlinks=follow_symlinks):
        dpath = Path(dirpath)
        if ignore_hidden and _is_hidden(dpath):
            # Skip hidden directories entirely
            dirnames[:] = []
            continue
        # Optionally skip hidden subdirs
        if ignore_hidden:
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        # Skip excluded directories
        if excluded_dirs:
            dirnames[:] = [d for d in dirnames if d.lower() not in excluded_dirs]
        for fn in filenames:
            p = dpath / fn
            if ignore_hidden and _is_hidden(p):
                continue
            ext = p.suffix.lower().lstrip(".")
            if ext in allowed:
                yield p
