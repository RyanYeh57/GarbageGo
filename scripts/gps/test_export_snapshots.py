"""Unit tests for export_snapshots.py.

Run: python -I -X utf8 scripts/gps/test_export_snapshots.py
(pytest-compatible, but needs no third-party package.)
"""
import csv
import gzip
import hashlib
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from export_snapshots import export  # noqa: E402

SCHEMA = """CREATE TABLE snapshots (id INTEGER PRIMARY KEY, source TEXT NOT NULL,
fetched_at TEXT NOT NULL, sha256 TEXT NOT NULL, n_records INTEGER, raw BLOB NOT NULL)"""
BODY = '[{"car":"KED-1385","time":"20261117T193953","location":"山腳里"}]'.encode("utf-8")


def make_db(tmp, rows):
    """rows: (id, fetched_at, body, sha_override)"""
    path = Path(tmp) / "garbage.db"
    con = sqlite3.connect(path)
    con.execute(SCHEMA)
    for i, fetched_at, body, sha in rows:
        con.execute(
            "INSERT INTO snapshots VALUES (?, 'taichung', ?, ?, ?, ?)",
            (i, fetched_at, sha or hashlib.sha256(body).hexdigest(),
             0 if body == b"[]" else 1, gzip.compress(body)),
        )
    con.commit()
    con.close()
    return path


def read_csv(out):
    with open(out / "collected_at.csv", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_bytes_and_collected_at_kept():
    with tempfile.TemporaryDirectory() as tmp:
        db = make_db(tmp, [(1, "2026-11-17T19:42:00+08:00", BODY, None)])
        out = Path(tmp) / "out"
        assert export(db, out) == (1, 0, [])
        rows = read_csv(out)
        assert rows == [{"file": "20261117T194200_00001.json",
                         "collected_at": "2026-11-17T19:42:00+08:00"}]
        assert (out / rows[0]["file"]).read_bytes() == BODY


def test_empty_snapshot_still_written():
    # Task 5 counts empty arrays as skipped_files, so they must reach it.
    with tempfile.TemporaryDirectory() as tmp:
        db = make_db(tmp, [(1, "2026-11-17T19:42:00+08:00", b"[]", None)])
        assert export(db, Path(tmp) / "out") == (1, 1, [])


def test_sha_mismatch_not_written():
    with tempfile.TemporaryDirectory() as tmp:
        db = make_db(tmp, [(1, "2026-11-17T19:42:00+08:00", BODY, "0" * 64),
                           (2, "2026-11-17T19:47:00+08:00", BODY, None)])
        out = Path(tmp) / "out"
        assert export(db, out) == (1, 0, [1])
        assert [r["file"] for r in read_csv(out)] == ["20261117T194700_00002.json"]


def test_date_filter_uses_taipei_date():
    from datetime import date
    with tempfile.TemporaryDirectory() as tmp:
        db = make_db(tmp, [(1, "2026-11-16T23:58:00+08:00", BODY, None),
                           (2, "2026-11-17T00:03:00+08:00", BODY, None)])
        out = Path(tmp) / "out"
        assert export(db, out, date(2026, 11, 17)) == (1, 0, [])
        assert read_csv(out)[0]["file"].endswith("_00002.json")


def test_refuses_non_empty_out_dir():
    with tempfile.TemporaryDirectory() as tmp:
        db = make_db(tmp, [(1, "2026-11-17T19:42:00+08:00", BODY, None)])
        out = Path(tmp) / "out"
        out.mkdir()
        (out / "old.json").write_text("[]")
        try:
            export(db, out)
        except ValueError as e:
            assert "not empty" in str(e)
        else:
            raise AssertionError("expected ValueError")


def test_missing_timezone_aborts():
    with tempfile.TemporaryDirectory() as tmp:
        db = make_db(tmp, [(1, "2026-11-17T19:42:00", BODY, None)])
        try:
            export(db, Path(tmp) / "out")
        except ValueError as e:
            assert "timezone" in str(e)
        else:
            raise AssertionError("expected ValueError")


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print("PASS", t.__name__)
        except Exception as e:  # noqa: BLE001
            failed += 1
            print("FAIL", t.__name__, type(e).__name__, e)
    print(f"{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
