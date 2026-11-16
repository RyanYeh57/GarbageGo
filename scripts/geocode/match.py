"""Local address matching: 84004 collection points vs Taichung GIS address points.

Data is NOT in Git (large, re-downloadable). Download first:
  - 84004 JSON: https://data.gov.tw/dataset/84004
  - Taichung GIS address points (monthly CSV via Google Drive links in the
    catalog): https://data.gov.tw/dataset/169806

Usage: python -I -X utf8 match.py <addr_csv> <pts_json> <out_dir>
Details and results: docs/research/geocoding-local-match-trial.md
"""
import collections
import csv
import json
import random
import re
import sys
from pathlib import Path

CN_DIGIT = {"零": 0, "〇": 0, "一": 1, "二": 2, "兩": 2, "三": 3, "四": 4,
            "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
CN_UNIT = {"十": 10, "百": 100, "千": 1000}
CN_RUN = re.compile(r"[零〇一二兩三四五六七八九十百千]+")
FW = str.maketrans("０１２３４５６７８９－", "0123456789-")


def cn_to_int(s):
    if not any(ch in CN_UNIT for ch in s):  # digit-by-digit, e.g. 一〇五
        return int("".join(str(CN_DIGIT[ch]) for ch in s))
    total, cur = 0, 0
    for ch in s:
        if ch in CN_DIGIT:
            cur = CN_DIGIT[ch]
        else:
            total += (cur or 1) * CN_UNIT[ch]
            cur = 0
    return total + cur


def canon(s):
    """Same normalisation for both sides so keys compare."""
    s = s.translate(FW).replace(" ", "").replace("　", "")
    s = s.replace("臺", "台").replace("壳", "殼")
    s = s.replace("-", "之")
    return CN_RUN.sub(lambda m: str(cn_to_int(m.group())), s)


def strip_after_hao(num):
    i = num.find("號")
    return num[: i + 1] if i >= 0 else num


NOTE = re.compile(r"[（(][^）)]*[）)]")
SUB_AFTER_HAO = re.compile(r"(\d+)號((?:之\d+)+)")  # 15號之3 -> 15之3號
SUFFIX = re.compile(r"號(.+)$")
NUM_TAIL = re.compile(r"^(?P<prefix>.*?)(?P<num>\d+(?:之\d+)*)號$")


def parse_caption(caption, village=""):
    """Return (canonical_full, flags) or (None, flags)."""
    flags = []
    s = caption
    if NOTE.search(s):
        flags.append("note")
        s = NOTE.sub("", s)
    s = canon(s)
    v = canon(village)
    if v and s.startswith(v):
        flags.append("village_prefix")
        s = s[len(v):]
    s = SUB_AFTER_HAO.sub(r"\1\2號", s)
    m = SUFFIX.search(s)
    if m:
        flags.append("suffix:" + m.group(1))
        s = s[: m.start() + 1]
    if not NUM_TAIL.match(s):
        flags.append("no_number")
        return None, flags
    return s, flags


def load_addr(path):
    by_key = {}
    by_prefix = collections.defaultdict(list)  # (code, prefix) -> [(base_num, row)]
    villages = collections.defaultdict(set)
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            code = row["鄉鎮市區代碼"]
            villages[code].add(row["村里"])
            num = strip_after_hao(row["號"])
            full = canon(row["街、路段"] + row["地區"] + row["巷"] + row["弄"] + num)
            rec = (float(row["WGS84經度"] or 0), float(row["WGS84緯度"] or 0), row["村里"])
            by_key.setdefault((code, full), rec)
            m = NUM_TAIL.match(full)
            if m:
                base = int(m.group("num").split("之")[0])
                by_prefix[(code, m.group("prefix"))].append((base, rec))
    return by_key, by_prefix, villages


def area_codes(pts, villages):
    """Map 84004 area name -> district code by village overlap (no hard-coding)."""
    votes = collections.defaultdict(collections.Counter)
    for p in pts:
        for code, vs in villages.items():
            if p["village"] in vs:
                votes[p["area"]][code] += 1
    return {a: c.most_common(1)[0][0] for a, c in votes.items()}


def match_one(p, code, by_key, by_prefix):
    full, flags = parse_caption(p["caption"], p["village"])
    if full is None:
        return "no_number", None, flags
    if (code, full) in by_key:
        level = "approx_suffix" if any(f.startswith("suffix") for f in flags) else "exact"
        return level, by_key[(code, full)], flags
    m = NUM_TAIL.match(full)
    prefix, num = m.group("prefix"), m.group("num")
    if "之" in num:
        base = f"{prefix}{num.split('之')[0]}號"
        if (code, base) in by_key:
            return "approx_base_number", by_key[(code, base)], flags
    cands = by_prefix.get((code, prefix))
    if not cands:
        return "street_not_found", None, flags
    target = int(num.split("之")[0])
    same_side = [c for c in cands if c[0] % 2 == target % 2] or cands
    best = min(same_side, key=lambda c: abs(c[0] - target))
    if abs(best[0] - target) <= 10:
        return "approx_nearby_number", best[1], flags + [f"used:{best[0]}號"]
    return "number_not_found", None, flags


def main():
    addr_path, pts_path, out_dir = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    out_dir.mkdir(parents=True, exist_ok=True)
    pts = json.load(open(pts_path, encoding="utf-8-sig"))
    by_key, by_prefix, villages = load_addr(addr_path)
    codes = area_codes(pts, villages)
    print(f"address points: {len(by_key):,} unique keys; districts mapped: {len(codes)}")

    results = []
    for p in pts:
        code = codes.get(p["area"])
        level, rec, flags = match_one(p, code, by_key, by_prefix)
        village_ok = None if rec is None else (rec[2] == p["village"])
        results.append({"area": p["area"], "village": p["village"], "task_type": p["task_type"],
                        "caption": p["caption"], "level": level, "flags": ";".join(flags),
                        "lon": rec[0] if rec else "", "lat": rec[1] if rec else "",
                        "addr_village": rec[2] if rec else "", "village_ok": village_ok})

    random.seed(42)
    sample = random.sample(results, 200)

    def report(rows, title):
        c = collections.Counter(r["level"] for r in rows)
        n = len(rows)
        print(f"\n== {title} (n={n}) ==")
        for k in ["exact", "approx_suffix", "approx_base_number", "approx_nearby_number",
                  "number_not_found", "street_not_found", "no_number"]:
            print(f"{k:22s} {c[k]:6d} {c[k] / n:6.1%}")
        got = [r for r in rows if r["lon"] != ""]
        vok = sum(1 for r in got if r["village_ok"])
        print(f"{'matched total':22s} {len(got):6d} {len(got) / n:6.1%}")
        print(f"{'village agrees':22s} {vok:6d} {vok / max(len(got), 1):6.1%} of matched")
        by_type = collections.defaultdict(lambda: [0, 0])
        for r in rows:
            by_type[r["task_type"]][0] += 1
            by_type[r["task_type"]][1] += r["lon"] != ""
        for t, (tot, ok) in by_type.items():
            print(f"  task_type {t}: {ok}/{tot} matched ({ok / tot:.1%})")

    report(sample, "sample 200, seed 42")
    report(results, "all 84004 points")

    fields = list(results[0].keys())
    for name, rows in [("sample200.csv", sample), ("all.csv", results)]:
        with open(out_dir / name, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)

    print("\n-- sample failures --")
    for r in [r for r in sample if r["lon"] == ""][:25]:
        print(r["level"], "|", r["area"], r["village"], "|", r["caption"])


if __name__ == "__main__":
    main()
