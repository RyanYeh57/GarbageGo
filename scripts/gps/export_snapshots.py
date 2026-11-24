"""Export GPS snapshots from the old collector's SQLite into the folder format
that Task 5 (`app.modules.ingestion.gps`) imports.

Input: the old collector's `garbage.db` (NOT in Git). Only the `snapshots`
table is used: each row is one full 83558 API response (gzip of the original
JSON bytes) plus `fetched_at`, the time we fetched it.

Output (out_dir must be new or empty; keep it out of Git):
  <fetched_at compact>_<id>.json   original API array, bytes unchanged
  collected_at.csv                 file,collected_at  (= snapshots.fetched_at)

collected_at comes from `fetched_at`, never from file mtime
(docs/plans/2026-11-22-week1-backend-foundation.md, Task 5, decision 1).

Usage: python -I -X utf8 export_snapshots.py <garbage.db> <out_dir> [--date YYYY-MM-DD]
  --date  only export snapshots fetched on that Taipei date (Task 5 Step 5b)
"""
import argparse
import csv
import gzip
import hashlib
import sqlite3
import sys
from contextlib import closing
from datetime import date, datetime
from pathlib import Path

SOURCE = "taichung"


def file_name(snapshot_id, fetched_at):
    """'2026-10-05T21:01:05+08:00', 1 -> '20261005T210105_00001.json' (no ':' for Windows)."""
    return f"{fetched_at.strftime('%Y%m%dT%H%M%S')}_{snapshot_id:05d}.json"


def parse_fetched_at(s):
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        raise ValueError(f"fetched_at has no timezone: {s!r}")
    return dt


def export(db_path, out_dir, only_date=None):
    """Write snapshots to out_dir. Returns (written, empty, bad_ids)."""
    out_dir = Path(out_dir)
    if out_dir.exists() and any(out_dir.iterdir()):
        raise ValueError(f"out_dir is not empty: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)

    uri = Path(db_path).resolve().as_uri() + "?mode=ro"
    written, empty, bad_ids = 0, 0, []
    with closing(sqlite3.connect(uri, uri=True)) as con, \
            open(out_dir / "collected_at.csv", "w", newline="", encoding="utf-8") as f:
        rows = con.execute(
            "SELECT id, fetched_at, sha256, n_records, raw FROM snapshots "
            "WHERE source = ? ORDER BY fetched_at, id",
            (SOURCE,),
        )
        w = csv.writer(f)
        w.writerow(["file", "collected_at"])
        for snapshot_id, fetched_at_s, sha, n_records, raw in rows:
            fetched_at = parse_fetched_at(fetched_at_s)
            if only_date and fetched_at.date() != only_date:
                continue
            body = gzip.decompress(raw)
            if hashlib.sha256(body).hexdigest() != sha:
                bad_ids.append(snapshot_id)  # corrupted; let the caller decide
                continue
            name = file_name(snapshot_id, fetched_at)
            (out_dir / name).write_bytes(body)
            w.writerow([name, fetched_at_s])
            written += 1
            empty += n_records == 0
    return written, empty, bad_ids


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("db_path")
    p.add_argument("out_dir")
    p.add_argument("--date", type=date.fromisoformat)
    a = p.parse_args()

    written, empty, bad_ids = export(a.db_path, a.out_dir, a.date)
    print(f"written={written} empty_snapshots={empty} sha256_mismatch={len(bad_ids)}")
    if bad_ids:
        print("sha256 mismatch, NOT written (snapshot ids):", bad_ids)
        sys.exit(1)


if __name__ == "__main__":
    main()
