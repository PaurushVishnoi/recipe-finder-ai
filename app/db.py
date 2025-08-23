from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "recipes.db"

def get_conn():
    if not DB_PATH.exists():
        raise RuntimeError(f"DB not found at {DB_PATH}. Run scripts/init_db.py first.")
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn