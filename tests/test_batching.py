from src.utils import chunked


def test_chunked_basic():
    data = list(range(250))
    chunks = list(chunked(data, 100))
    assert len(chunks) == 3
    assert len(chunks[0]) == 100
    assert len(chunks[1]) == 100
    assert len(chunks[2]) == 50


def test_chunked_value_error():
    import pytest

    with pytest.raises(ValueError):
        list(chunked([1, 2, 3], 0))
