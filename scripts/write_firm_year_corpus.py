import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from urllib.parse import quote_plus

load_dotenv()  # Loads .env into environment variables

user = os.getenv("MYSQL_USER", "root")
pwd = os.getenv("MYSQL_PASSWORD", "")
host = os.getenv("MYSQL_HOST", "localhost")
port = os.getenv("MYSQL_PORT", "3306")
db   = os.getenv("MYSQL_DB", "fyp")

# URL-encode password (handles special characters safely)
pwd_enc = quote_plus(pwd)

engine = create_engine(f"mysql+pymysql://{user}:{pwd_enc}@{host}:{port}/{db}")

TABLE_OUT = "firm_year_corpus_01"

firm_year_corpus.write_database(
    table_name=TABLE_OUT,
    connection=engine,
    if_table_exists="fail",
)

print(f"Wrote table → {db}.{TABLE_OUT}")
