import abletonlivemcp


def test_version_is_semver():
    parts = abletonlivemcp.__version__.split(".")
    assert len(parts) == 3 and all(p.isdigit() for p in parts)
