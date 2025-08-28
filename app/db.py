from pathlib import Path
import sqlite3
from contextlib import closing
from typing import Any, Iterable

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "recipes.db"

def get_conn():
    if not DB_PATH.exists():
        raise RuntimeError(f"DB not found at {DB_PATH}. Run scripts/init_db.py first.")
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def fetch_all(sql: str, params: Iterable[Any] | dict | None = None) -> list[dict]:
    """
    Execute a SELECT and return a list of dicts.
    Accepts positional (tuple/list) or named (dict) params.
    """
    with closing(get_conn()) as conn:
        cur = conn.execute(sql, params or ())
        rows = cur.fetchall()
        # sqlite3.Row -> dict is supported because of row_factory above
        return [dict(row) for row in rows]

def fetch_val(sql: str, params: Iterable[Any] | dict | None = None) -> Any:
    """
    Execute a query expected to return a single scalar (e.g., COUNT(*)).
    Returns 0 if there is no row.
    """
    with closing(get_conn()) as conn:
        cur = conn.execute(sql, params or ())
        row = cur.fetchone()
        if row is None:
            return 0
        # If the row is a sqlite3.Row, grab the first column's value
        # (works whether it's aliased or not, e.g., COUNT(*) or COUNT(*) AS total_count)
        return row[0]
