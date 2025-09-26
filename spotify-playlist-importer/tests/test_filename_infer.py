from pathlib import Path

from src.metadata import infer_from_filename
from src.types import LocalTrack


def lt(path: str) -> LocalTrack:
    return LocalTrack(path=Path(path), title=None, artist=None, album=None, duration_ms=None, year=None, isrc=None)


def test_infer_artist_title_dash():
    l = infer_from_filename(Path("Artist - Title.flac"), lt("Artist - Title.flac"))
    assert l.artist == "Artist"
    assert l.title == "Title"


def test_infer_artist_title_underscore():
    l = infer_from_filename(Path("Artist_Title.mp3"), lt("Artist_Title.mp3"))
    assert l.artist == "Artist"
    assert l.title == "Title"


def test_strip_suffixes():
    l = infer_from_filename(Path("Artist - Title (Remastered 2011).mp3"), lt("Artist - Title (Remastered 2011).mp3"))
    assert l.title == "Title"
