from __future__ import annotations

import os
from pathlib import Path
from typing import List

import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth


def _load_env() -> None:
    # Load .env if present
    load_dotenv(override=False)


def get_spotify_client(scopes: List[str]):
    """Retourne un client Spotify authentifié (PKCE), avec cache & refresh.

    Variables d'env attendues:
    - SPOTIFY_CLIENT_ID
    - SPOTIFY_REDIRECT_URI
    """
    _load_env()

    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")
    if not client_id or not redirect_uri:
        raise RuntimeError(
            "SPOTIFY_CLIENT_ID et SPOTIFY_REDIRECT_URI doivent être configurés dans .env"
        )

    cache_dir = Path(".cache")
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = str(cache_dir / "token_cache")

    # Prefer PKCE first (no client secret). Fallback to OAuth in PKCE mode if needed.
    try:
        from spotipy.oauth2 import SpotifyPKCE  # type: ignore

        auth_manager = SpotifyPKCE(
            client_id=client_id,
            redirect_uri=redirect_uri,
            scope=" ".join(scopes),
            open_browser=True,
            cache_path=cache_path,
        )
    except Exception:
        auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=None,
            redirect_uri=redirect_uri,
            scope=" ".join(scopes),
            open_browser=True,
            cache_path=cache_path,
            show_dialog=True,
        )
    return spotipy.Spotify(auth_manager=auth_manager)
