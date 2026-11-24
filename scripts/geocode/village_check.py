"""Sanity check: for matched points whose village differs, how far is the point
from the centroid of the 84004-claimed village's address points?

Usage: python -I -X utf8 village_check.py <addr_csv> <all_csv> <suspects_out_csv>
suspects_out_csv: source_index,distance_m for points > 3 km from the claimed village.
"""
import collections
import csv
import math
import sys


def load_centroids(addr_path):
    """village name -> [(lon, lat)] centroids, one per (district, village)."""
    sums = collections.defaultdict(lambda: [0.0, 0.0, 0])
    with open(addr_path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            if r["WGS84經度"]:
                s = sums[(r["鄉鎮市區代碼"], r["村里"])]
                s[0] += float(r["WGS84經度"]); s[1] += float(r["WGS84緯度"]); s[2] += 1
    cent_by_village = collections.defaultdict(list)
    for (code, v), (x, y, n) in sums.items():
        cent_by_village[v].append((x / n, y / n))
    return cent_by_village


def dist_m(a, b):
    dx = (a[0] - b[0]) * 111320 * math.cos(math.radians(a[1]))
    dy = (a[1] - b[1]) * 110540
    return math.hypot(dx, dy)


def nearest_claimed(r, cent_by_village):
    """Distance (m) from a matched, village-mismatched row to its claimed village; None if n/a."""
    if not r["lon"] or r["village_ok"] == "True":
        return None
    cs = cent_by_village.get(r["village"])
    if not cs:
        return None
    p = (float(r["lon"]), float(r["lat"]))
    return min(dist_m(p, c) for c in cs)


def find_suspects(rows, cent_by_village, threshold_m=3000):
    """[(source_index, distance_m)] for rows farther than threshold_m from the claimed village."""
    out = []
    for r in rows:
        d = nearest_claimed(r, cent_by_village)
        if d is not None and d > threshold_m:
            out.append((int(r["source_index"]), round(d)))
    return out


def main():
    addr_path, all_path, suspects_path = sys.argv[1], sys.argv[2], sys.argv[3]
    cent_by_village = load_centroids(addr_path)
    rows = list(csv.DictReader(open(all_path, encoding="utf-8-sig")))

    by_level = collections.defaultdict(lambda: [0, 0])
    buckets = collections.Counter()
    for r in rows:
        if not r["lon"]:
            continue
        by_level[r["level"]][0] += 1
        if r["village_ok"] == "True":
            continue
        by_level[r["level"]][1] += 1
        if not cent_by_village.get(r["village"]):
            buckets["claimed village not in address data"] += 1
            continue
        d = nearest_claimed(r, cent_by_village)
        buckets["<500m" if d < 500 else "500m-1km" if d < 1000 else "1-3km" if d < 3000 else ">3km"] += 1
    print("village mismatch by level:")
    for k, (tot, mis) in by_level.items():
        print(f"  {k:22s} {mis}/{tot} ({mis / tot:.1%})")
    print("mismatch: distance to claimed village centroid:", dict(buckets))

    suspects = find_suspects(rows, cent_by_village)
    with open(suspects_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["source_index", "distance_m"])
        w.writerows(suspects)
    print(f"suspects (>3km): {len(suspects)} -> {suspects_path}")


if __name__ == "__main__":
    main()
