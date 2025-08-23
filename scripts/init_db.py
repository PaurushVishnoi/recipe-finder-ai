#!/usr/bin/env python3
"""
Initialize the SQLite database for the Recipe Finder app.

- Creates data/recipes.db (if missing)
- Creates the `recipes` table (if missing)
- Imports data from data/recipes-en.json ONLY if the table is empty
- Optional: --force  -> truncates then re-imports
"""
import argparse
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "recipes.db"
JSON_PATH = ROOT / "data" / "recipes-en.json"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS recipes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  -- Optional uniqueness to avoid dup inserts across runs
  -- If your dataset has reliable unique titles, keep this UNIQUE.
  -- Otherwise, comment it out or switch to a slug field later.
  title TEXT NOT NULL UNIQUE,
  cook_time INTEGER,
  prep_time INTEGER,
  ratings REAL,
  cuisine TEXT,
  category TEXT,
  author TEXT,
  image TEXT,
  ingredients_json TEXT NOT NULL
);
"""

def connect_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

def table_rowcount(conn: sqlite3.Connection) -> int:
    cur = conn.execute("SELECT COUNT(*) FROM recipes;")
    return cur.fetchone()[0]

def create_schema(conn: sqlite3.Connection) -> None:
    conn.execute(SCHEMA_SQL)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_recipes_title ON recipes(title);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_recipes_category ON recipes(category);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_recipes_cuisine ON recipes(cuisine);")
    conn.commit()

def load_json() -> list[dict]:
    if not JSON_PATH.exists():
        raise FileNotFoundError(f"JSON file not found at: {JSON_PATH}")
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Expected a JSON array of recipe objects.")
    return data

def as_int(x):
    try:
        return int(x) if x not in (None, "") else None
    except:
        return None

def as_float(x):
    try:
        return float(x) if x not in (None, "") else None
    except:
        return None

def normalize(recipe: dict) -> dict:
    return {
        "title": recipe.get("title"),
        "cook_time": as_int(recipe.get("cook_time")),
        "prep_time": as_int(recipe.get("prep_time")),
        "ratings": as_float(recipe.get("ratings")),
        "cuisine": recipe.get("cuisine"),
        "category": recipe.get("category"),
        "author": recipe.get("author"),
        "image": recipe.get("image"),
        "ingredients_json": json.dumps(recipe.get("ingredients", []), ensure_ascii=False),
    }

def bulk_insert(conn: sqlite3.Connection, recipes: list[dict]) -> int:
    sql = """
    INSERT OR IGNORE INTO recipes
    (title, cook_time, prep_time, ratings, cuisine, category, author, image, ingredients_json)
    VALUES
    (:title, :cook_time, :prep_time, :ratings, :cuisine, :category, :author, :image, :ingredients_json)
    """
    rows = [normalize(r) for r in recipes]
    with conn:
        cur = conn.executemany(sql, rows)
    # executemany returns a cursor; rowcount can be -1 for batch inserts.
    # We derive inserted count from delta in table size afterwards.
    return len(rows)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Truncate the table before import.")
    args = parser.parse_args()

    conn = connect_db()
    create_schema(conn)

    # Ensure the table exists before counting
    try:
        existing = table_rowcount(conn)
    except sqlite3.OperationalError:
        existing = 0

    if args.force and existing > 0:
        with conn:
            conn.execute("DELETE FROM recipes;")
        print("⚠️  Cleared existing rows (force mode).")
        existing = 0

    if existing > 0:
        print(f"✅ Table already populated with {existing} rows. Nothing to do.")
        conn.close()
        return

    data = load_json()
    before = table_rowcount(conn) if existing == 0 else existing
    bulk_insert(conn, data)
    after = table_rowcount(conn)
    print(f"✅ Imported {after - before} new recipes (total: {after}) into {DB_PATH}")
    conn.close()

if __name__ == "__main__":
    main()
