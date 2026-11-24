from app.core.config import get_settings, load_dotenv


def test_day_index_mapping_matches_research():
    # Values from docs/research/opendata-api-check.md §10 (d1..d7 = Monday..Sunday)
    assert get_settings().schedule_day_index_to_iso_weekday == {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7}


def test_load_dotenv_skips_comments(tmp_path):
    p = tmp_path / ".env"
    p.write_text("# note\n\nA=1\nB=x=y\n", encoding="utf-8")
    assert load_dotenv(p) == {"A": "1", "B": "x=y"}


def test_load_dotenv_missing_file(tmp_path):
    assert load_dotenv(tmp_path / "nope.env") == {}
