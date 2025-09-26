from src.matcher import score_candidate
from src.types import Candidate, LocalTrack
from pathlib import Path


def test_score_prefers_exact_title_and_artist():
    lt = LocalTrack(path=Path("x"), title="Song A", artist="Artist B", album=None, duration_ms=220000, year=2020, isrc=None)
    cand_good = Candidate(uri="u1", name="Song A", artists=["Artist B"], album="Album", duration_ms=220000, score=0.0, release_year=2020)
    cand_bad = Candidate(uri="u2", name="Another Song", artists=["Other"], album="Album", duration_ms=250000, score=0.0, release_year=2010)

    s_good = score_candidate(lt, cand_good)
    s_bad = score_candidate(lt, cand_bad)

    assert s_good > s_bad
    assert s_good > 0.9


def test_duration_within_3s_full_score():
    lt = LocalTrack(path=Path("x"), title="X", artist="Y", album=None, duration_ms=180000, year=None, isrc=None)
    cand = Candidate(uri="u", name="X", artists=["Y"], album="A", duration_ms=182500, score=0.0)
    s = score_candidate(lt, cand)
    assert s > 0.9
