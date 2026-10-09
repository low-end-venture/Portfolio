"""Reference solution. Try etl_exercise.py first -- peek here only when stuck."""

import csv
import sqlite3
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y")


def extract(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def clean_text(value):
    collapsed = " ".join(value.split())
    return collapsed.title() if collapsed else None


def parse_date(value):
    value = value.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def parse_quantity(value):
    try:
        qty = int(value.strip())
    except ValueError:
        return None
    return qty if qty > 0 else None


def parse_price_cents(value):
    cleaned = value.strip().replace("$", "").replace(",", "")
    try:
        price = Decimal(cleaned)
    except InvalidOperation:
        return None
    if not price.is_finite() or price < 0 or price.as_tuple().exponent < -2:
        return None
    return int(price * 100)


def transform(rows):
    clean, rejects = [], []
    seen_ids = set()

    for row in rows:
        try:
            order_id = int(row["order_id"].strip())
        except ValueError:
            rejects.append({"row": row, "reason": "bad order_id"})
            continue

        record = {
            "order_id": order_id,
            "order_date": parse_date(row["order_date"]),
            "customer": clean_text(row["customer"]),
            "region": clean_text(row["region"]),
            "product": clean_text(row["product"]),
            "quantity": parse_quantity(row["quantity"]),
            "unit_price_cents": parse_price_cents(row["unit_price"]),
        }

        missing = [k for k, v in record.items() if v is None]
        if missing:
            rejects.append({"row": row, "reason": "invalid " + ", ".join(missing)})
        elif order_id in seen_ids:
            rejects.append({"row": row, "reason": "duplicate order_id"})
        else:
            seen_ids.add(order_id)
            clean.append(record)

    return clean, rejects


def load(records, db_path):
    conn = sqlite3.connect(db_path)
    try:
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    order_id         INTEGER PRIMARY KEY,
                    order_date       TEXT    NOT NULL,
                    customer         TEXT    NOT NULL,
                    region           TEXT    NOT NULL,
                    product          TEXT    NOT NULL,
                    quantity         INTEGER NOT NULL CHECK (quantity > 0),
                    unit_price_cents INTEGER NOT NULL CHECK (unit_price_cents >= 0)
                )
                """
            )
            conn.executemany(
                """
                INSERT OR REPLACE INTO orders
                VALUES (:order_id, :order_date, :customer, :region,
                        :product, :quantity, :unit_price_cents)
                """,
                [{**r, "order_date": r["order_date"].isoformat()} for r in records],
            )
    finally:
        conn.close()


def revenue_by_region(db_path):
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute(
            """
            SELECT region, SUM(quantity * unit_price_cents) AS revenue_cents
            FROM orders
            GROUP BY region
            ORDER BY revenue_cents DESC, region
            """
        ).fetchall()
    finally:
        conn.close()


def main():
    here = Path(__file__).resolve().parent.parent
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
