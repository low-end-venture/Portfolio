"""Self-check for the exercise. Run:  python test_etl.py

Every test runs even if earlier ones fail, so you can work one function at a time.
To check the reference solution instead:  ETL_MODULE=solution.etl_solution python test_etl.py
"""

import importlib
import os
import sqlite3
import tempfile
import traceback
from datetime import date
from pathlib import Path

etl = importlib.import_module(os.environ.get("ETL_MODULE", "etl_exercise"))
RAW_CSV = Path(__file__).resolve().parent / "data" / "orders_raw.csv"


def test_extract():
    rows = etl.extract(RAW_CSV)
    assert len(rows) == 10, f"expected 10 rows, got {len(rows)}"
    assert rows[0]["order_id"] == "1001"
    assert rows[1]["unit_price"] == "$1,200.00", "quoted comma must stay inside one field"


def test_clean_text():
    assert etl.clean_text("  acme   corp ") == "Acme Corp"
    assert etl.clean_text("SOUTH") == "South"
    assert etl.clean_text("   ") is None
    assert etl.clean_text("") is None


def test_parse_date():
    assert etl.parse_date("2026-01-05") == date(2026, 1, 5)
    assert etl.parse_date("01/06/2026") == date(2026, 1, 6)
    assert etl.parse_date("2026-13-01") is None
    assert etl.parse_date("") is None


def test_parse_quantity():
    assert etl.parse_quantity("10") == 10
    assert etl.parse_quantity(" 3 ") == 3
    assert etl.parse_quantity("") is None
    assert etl.parse_quantity("-4") is None
    assert etl.parse_quantity("0") is None
    assert etl.parse_quantity("2.5") is None


def test_parse_price_cents():
    assert etl.parse_price_cents("$12.50") == 1250
    assert etl.parse_price_cents("$1,200.00") == 120000
    assert etl.parse_price_cents("40") == 4000
    assert etl.parse_price_cents("0.10") == 10, "0.10 must be exactly 10 cents (no float drift)"
    assert etl.parse_price_cents("abc") is None
    assert etl.parse_price_cents("-5") is None
    assert etl.parse_price_cents("1.005") is None, "sub-cent prices are rejected, not rounded"
    assert etl.parse_price_cents("NaN") is None


def test_transform():
    clean, rejects = etl.transform(etl.extract(RAW_CSV))
    assert [r["order_id"] for r in clean] == [1001, 1002, 1004, 1007]
    assert len(rejects) == 6, f"expected 6 rejects, got {len(rejects)}"
    assert clean[0] == {
        "order_id": 1001,
        "order_date": date(2026, 1, 5),
        "customer": "Acme Corp",
        "region": "North",
        "product": "Widget",
        "quantity": 10,
        "unit_price_cents": 1250,
    }
    assert all(r["reason"] for r in rejects), "every reject needs a reason"


def test_load_and_report():
    clean, _ = etl.transform(etl.extract(RAW_CSV))
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "orders.db"
        etl.load(clean, db)
        etl.load(clean, db)  # running twice must not duplicate rows
        conn = sqlite3.connect(db)
        try:
            count = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        finally:
            conn.close()
        assert count == 4, f"load is not idempotent: {count} rows after two loads"
        assert etl.revenue_by_region(db) == [
            ("North", 372500),
            ("South", 120000),
            ("East", 20000),
        ]


if __name__ == "__main__":
    tests = [(n, f) for n, f in globals().items() if n.startswith("test_")]
    passed = 0
    for name, fn in tests:
        try:
            fn()
        except NotImplementedError:
            print(f"TODO  {name}")
        except Exception:
            print(f"FAIL  {name}")
            print("      " + traceback.format_exc().strip().splitlines()[-1])
        else:
            passed += 1
            print(f"PASS  {name}")
    print(f"\n{passed}/{len(tests)} passing")
