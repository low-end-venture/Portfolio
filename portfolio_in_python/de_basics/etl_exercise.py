"""ETL practice: messy CSV -> clean records -> SQLite -> report.

Fill in each function (delete the `raise NotImplementedError` line), then run:
    python test_etl.py
Work top to bottom; each function builds on the ones above it.
"""

import csv
import sqlite3
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path


# --- EXTRACT ---------------------------------------------------------------

def extract(path):
    """Read the CSV at `path` and return a list of dicts, one per row.

    Every value stays a string -- no cleaning here. Extract is dumb on purpose.
    M equivalent:  Csv.Document(...) + Table.PromoteHeaders

    Hint: open(path, newline="", encoding="utf-8") and csv.DictReader.
          Don't split on commas yourself -- "$1,200.00" has a comma in it.
    """
    raise NotImplementedError


# --- TRANSFORM: one small parser per column type ---------------------------
# Each parser takes a raw string and returns a clean value, or None if the
# value is unusable. Returning None (instead of crashing) lets transform()
# collect every bad row with a reason.

def clean_text(value):
    """Trim, collapse inner whitespace, Title Case. Blank -> None.

    "  acme   corp " -> "Acme Corp"      "SOUTH" -> "South"      "  " -> None
    M equivalent:  Text.Trim + Text.Proper

    Hint: " ".join(value.split()) collapses all runs of whitespace.
    """
    raise NotImplementedError


def parse_date(value):
    """Return a datetime.date, accepting "YYYY-MM-DD" or "MM/DD/YYYY". Else None.

    "2026-13-01" -> None (there is no month 13).

    Hint: datetime.strptime(value, fmt).date() raises ValueError on a mismatch.
          Loop over the formats; try/except each one.
    """
    raise NotImplementedError


def parse_quantity(value):
    """Return a positive int, else None.  "10" -> 10, "" / "-4" / "0" / "2.5" -> None"""
    raise NotImplementedError


def parse_price_cents(value):
    """Return the price as an int number of cents, else None.

    "$12.50" -> 1250     "$1,200.00" -> 120000     "40" -> 4000
    "abc" / "-5" / "NaN" / "1.005" (sub-cent) -> None

    Why cents and Decimal, not float?  Try  0.1 + 0.2  in the Python shell.
    Money stored as integer cents can never drift.

    Hint: strip "$" and ",", then Decimal(text) -- it raises InvalidOperation
          on garbage. Decimal("1.005").as_tuple().exponent == -3.
          Decimal has .is_finite().
    """
    raise NotImplementedError


def transform(rows):
    """Clean every raw row. Return (clean_records, rejects).

    clean record shape:
        {"order_id": 1001, "order_date": date(2026, 1, 5), "customer": "Acme Corp",
         "region": "North", "product": "Widget", "quantity": 10,
         "unit_price_cents": 1250}

    reject shape:
        {"row": <the original raw dict>, "reason": "invalid quantity"}

    Rules:
      - Any field that parses to None -> reject the row (say which field).
      - A valid row whose order_id was already accepted -> reject as duplicate.
        (Check duplicates against *accepted* ids, so a bad first copy doesn't
        block a good second copy.)
      - Never silently drop a row: len(clean) + len(rejects) == len(rows).
    """
    raise NotImplementedError


# --- LOAD ------------------------------------------------------------------

def load(records, db_path):
    """Write records into an `orders` table in the SQLite file at db_path.

    Must be idempotent: loading the same records twice leaves 4 rows, not 8.

    Hints:
      - sqlite3.connect(db_path); `with conn:` commits on success, rolls back on error.
      - CREATE TABLE IF NOT EXISTS ... order_id INTEGER PRIMARY KEY ...
      - INSERT OR REPLACE makes re-runs safe.
      - executemany with named placeholders (:order_id) -- never build SQL with
        f-strings from data.
      - SQLite has no date type: store order_date.isoformat().
      - Close the connection when done (try/finally).
    """
    raise NotImplementedError


# --- REPORT ----------------------------------------------------------------

def revenue_by_region(db_path):
    """Return [(region, revenue_cents), ...] sorted by revenue, highest first.

    Expected: [("North", 372500), ("South", 120000), ("East", 20000)]
    This one is mostly SQL -- you already know how to write it.
    """
    raise NotImplementedError


def main():
    here = Path(__file__).resolve().parent
    db_path = here / "orders.db"

    raw = extract(here / "data" / "orders_raw.csv")
    clean, rejects = transform(raw)
    load(clean, db_path)

    print(f"extracted {len(raw)}, loaded {len(clean)}, rejected {len(rejects)}")
    for r in rejects:
        print(f"  reject order_id={r['row']['order_id']!r}: {r['reason']}")
    print("\nrevenue by region:")
    for region, cents in revenue_by_region(db_path):
        dollars = f"${cents // 100:,}.{cents % 100:02d}"
        print(f"  {region:<8} {dollars:>12}")


if __name__ == "__main__":
    main()
