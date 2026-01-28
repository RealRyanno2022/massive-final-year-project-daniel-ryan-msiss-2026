# scripts/write_firm_year_corpus.py
from pathlib import Path
import os
from urllib.parse import quote_plus

import polars as pl
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


# --------------------
# Paths / inputs
# --------------------
OUT_DIR = Path("outputs")
OUT_DIR.mkdir(parents=True, exist_ok=True)

CSV_IN = OUT_DIR / "firm_year_corpus.csv"   # must exist
TABLE_PREFIX = "firm_year_corpus_"          # writes firm_year_corpus_01, _02, ...


# --------------------
# Env / DB connect
# --------------------
load_dotenv()

user = os.getenv("MYSQL_USER", "root")
pwd = os.getenv("MYSQL_PASSWORD", "")
host = os.getenv("MYSQL_HOST", "localhost")
port = os.getenv("MYSQL_PORT", "3306")
db   = os.getenv("MYSQL_DB", "fyp")

engine = create_engine(
    f"mysql+pymysql://{user}:{quote_plus(pwd)}@{host}:{port}/{db}"
)


# --------------------
# Load artefact (CSV) + force types before MySQL write
# --------------------
if not CSV_IN.exists():
    raise FileNotFoundError(f"Missing input CSV: {CSV_IN.resolve()}")

firm_year_corpus = pl.read_csv(CSV_IN).with_columns(
    pl.col("ticker").cast(pl.Utf8),
    pl.col("cik").cast(pl.Utf8),          # IMPORTANT: keep as string so indexing works
    pl.col("gics_sector").cast(pl.Utf8),
    pl.col("year").cast(pl.Int32),
)


# --------------------
# Next versioned table name
# --------------------
with engine.connect() as conn:
    existing = [r[0] for r in conn.execute(text("SHOW TABLES")).fetchall()]

nums = []
for t in existing:
    if t.startswith(TABLE_PREFIX):
        try:
            nums.append(int(t.replace(TABLE_PREFIX, "")))
        except ValueError:
            pass

next_n = (max(nums) + 1) if nums else 1
TABLE_OUT = f"{TABLE_PREFIX}{next_n:02d}"


# --------------------
# Write table (no overwrite)
# --------------------
firm_year_corpus.write_database(
    table_name=TABLE_OUT,
    connection=engine,
    if_table_exists="fail",
)

print(f"Wrote table → {db}.{TABLE_OUT}")


# --------------------
# Indexes (clean failure, no stack trace spam)
# --------------------
def try_exec(conn, stmt: str) -> None:
    try:
        conn.execute(text(stmt))
        print(f"Index OK → {stmt}")
    except Exception as e:
        print(f"Index skipped → {str(e).splitlines()[0]}")

with engine.begin() as conn:
    try_exec(conn, f"CREATE INDEX idx_{TABLE_OUT}_ticker_year ON {TABLE_OUT} (ticker(16), year)")
    try_exec(conn, f"CREATE INDEX idx_{TABLE_OUT}_cik_year ON {TABLE_OUT} (cik(16), year)")
    try_exec(conn, f"CREATE INDEX idx_{TABLE_OUT}_sector_year ON {TABLE_OUT} (gics_sector(32), year)")
