from app.core.config import load_dotenv


def test_load_dotenv_skips_comments(tmp_path):
    p = tmp_path / ".env"
    p.write_text("# note\n\nA=1\nB=x=y\n", encoding="utf-8")
    assert load_dotenv(p) == {"A": "1", "B": "x=y"}


def test_load_dotenv_missing_file(tmp_path):
    assert load_dotenv(tmp_path / "nope.env") == {}
