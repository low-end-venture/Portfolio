# Python data engineering basics

A tiny ETL pipeline using only the standard library (no pandas):

```
data/orders_raw.csv  --extract-->  list of dicts  --transform-->  clean + rejects  --load-->  orders.db (SQLite)  -->  report
```

The raw CSV is deliberately messy: stray whitespace, mixed casing, two date
formats, `$` and `,` in prices, a blank quantity, a negative quantity, an
impossible date, a non-numeric price, a blank customer, and a duplicate row.

## How to practice

1. Open `etl_exercise.py` and fill in the functions top to bottom.
2. Run `python test_etl.py` after each one. You'll see `PASS` / `FAIL` / `TODO` per function.
3. When all 7 pass, run `python etl_exercise.py` for the full pipeline.
4. Stuck? `solution/etl_solution.py` has a reference answer.

## Ideas worth noticing

- **Extract is dumb, transform is strict.** Keep raw strings until one place decides what's valid.
- **Reject, don't drop.** Every bad row comes out with a reason; rows in = clean + rejects.
- **Money in integer cents.** Floats can't represent 0.10 exactly.
- **Idempotent loads.** Re-running the pipeline gives the same result, not doubled rows.
- **Parameterized SQL.** Never paste data into SQL strings.
