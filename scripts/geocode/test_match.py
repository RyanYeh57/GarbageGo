"""Unit tests for match.py normalisation and parsing.

Run: python -I -X utf8 scripts/geocode/test_match.py
(pytest-compatible, but needs no third-party package.)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from match import build_results, canon, cn_to_int, parse_caption, strip_after_hao  # noqa: E402
from village_check import find_suspects  # noqa: E402


def test_build_results_carries_source_index():
    pts = [{"area": "中區", "village": "中華里", "task_type": "沿街", "caption": "中華路一段143號"},
           {"area": "中區", "village": "中華里", "task_type": "沿街", "caption": "中華路一段145號"}]
    rows = build_results(pts, {}, {}, {})
    assert [r["source_index"] for r in rows] == [0, 1]
    assert list(rows[0])[0] == "source_index"


def test_find_suspects_threshold():
    rows = [{"source_index": "0", "lon": "120.68", "lat": "24.14", "village": "中華里", "village_ok": "False"},
            {"source_index": "1", "lon": "120.68", "lat": "24.14", "village": "中華里", "village_ok": "True"}]
    cents = {"中華里": [(120.68, 24.18)]}          # about 4.4 km
    assert [i for i, _ in find_suspects(rows, cents)] == [0]


def test_cn_to_int():
    assert cn_to_int("十") == 10
    assert cn_to_int("十七") == 17
    assert cn_to_int("二十三") == 23
    assert cn_to_int("一百零五") == 105
    assert cn_to_int("一〇五") == 105


def test_canon_same_on_both_sides():
    assert canon("美村路二段２７８號") == "美村路2段278號"
    assert canon("松順1街129號") == canon("松順一街１２９號")
    assert canon("臺中路58-5號") == "台中路58之5號"
    assert canon("龜壳路") == canon("龜殼路")


def test_strip_floor_from_address_number():
    assert strip_after_hao("５號三樓之１") == "５號"


def test_parse_note_and_suffix():
    assert parse_caption("青海路一段60號(福壽宮前)") == ("青海路1段60號", ["note"])
    assert parse_caption("中山路100號前") == ("中山路100號", ["suffix:前"])


def test_parse_no_number():
    assert parse_caption("中山路與民生路口")[0] is None


def test_parse_leading_village_removed():
    full, flags = parse_caption("福山里沙田路一段428巷63-23號(定點)", village="福山里")
    assert full == "沙田路1段428巷63之23號"
    assert "village_prefix" in flags


def test_parse_leading_village_kept_when_different():
    # only strip the 84004 village itself, never an arbitrary "XX里"
    assert parse_caption("福山里路5號", village="中山里")[0] == "福山里路5號"


def test_parse_sub_number_after_hao():
    full, flags = parse_caption("成功二路120巷15號之3")
    assert full == "成功2路120巷15之3號"
    assert not any(f.startswith("suffix") for f in flags)


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
