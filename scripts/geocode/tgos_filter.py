"""Keep only reliable TGOS fuzzy answers before importing them.

A row is kept when every answer TGOS returned is on the same street/lane as the address we sent
and its door number is within MAX_NUMBER_GAP (same limit as match.py approx_nearby_number).
Rejected rows keep id/Address but get blank Response_X/Response_Y, so the importer counts them as unmatched.

Usage: python -I -X utf8 scripts/geocode/tgos_filter.py <tgos_result.csv> <filtered.csv>
Then:  python -m app.modules.ingestion.tgos import --result <filtered.csv>   (from backend/)
"""
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from match import NUM_TAIL, canon, parse_caption  # noqa: E402

MAX_NUMBER_GAP = 10
CITY_DISTRICT = re.compile(r"^(臺中市|台中市)[^區]{1,3}區")
VILLAGE_NEIGHBOUR = re.compile(r"^[^\d;]{1,5}?里\d+鄰")


def _street_and_number(address: str, sent: bool) -> tuple[str, int] | None:
    s = CITY_DISTRICT.sub("", address.strip())
    if sent:
        s, _ = parse_caption(s)          # drops notes, 號前/號旁 suffixes, fixes 15號之3
        if s is None:
            return None
    else:
        s = canon(VILLAGE_NEIGHBOUR.sub("", s))
    m = NUM_TAIL.match(s)
    return (m.group("prefix"), int(m.group("num").split("之")[0])) if m else None


def accept(row: dict) -> bool:
    if not (row.get("Response_X") or "").strip():
        return False
    sent = _street_and_number(row["Address"], sent=True)
    if sent is None:
        return False
    for answer in row["Response_Address"].split(";"):
        got = _street_and_number(answer, sent=False)
        if got is None or got[0] != sent[0] or abs(got[1] - sent[1]) > MAX_NUMBER_GAP:
            return False
    return True


def main():
    src, dst = sys.argv[1], sys.argv[2]
    with open(src, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields, rows = reader.fieldnames, list(reader)
    kept = 0
    for r in rows:
        if accept(r):
            kept += 1
        else:
            r["Response_X"] = r["Response_Y"] = ""
    with open(dst, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"rows {len(rows)}, kept {kept}, blanked {len(rows) - kept} -> {dst}")


if __name__ == "__main__":
    main()
