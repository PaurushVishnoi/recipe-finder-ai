# app/main.py
from pathlib import Path
import json
from urllib.parse import urlparse, parse_qs, unquote

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .db import get_conn
from .llm_sql import nl_to_sql, clean_sql

app = FastAPI(title="Recipe Finder AI")

# ----- Serve frontend -----
FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
def root():
    index = FRONTEND_DIR / "index.html"
    if not index.exists():
        return JSONResponse({"error": "frontend not found"}, status_code=404)
    return FileResponse(index)


# ----- Models -----
class SearchBody(BaseModel):
    q: str
    limit: int | None = None


# ----- Health -----
@app.get("/api/health")
def health():
    return {"ok": True}


# ----- Image proxy (bypass strict CORS/CDNs safely with allowlist) -----
ALLOWED_IMAGE_HOSTS = {
    "imagesvc.meredithcorp.io",
    "images.media-allrecipes.com",
    "img.taste.com.au",
    "www.allrecipes.com",
}

@app.get("/img")
async def proxy_image(url: str = Query(..., description="Absolute image URL")):
    # Unwrap Meredith transformer URLs
    try:
        parsed = urlparse(url)
        if parsed.hostname == "imagesvc.meredithcorp.io":
            qs = parse_qs(parsed.query)
            inner = qs.get("url", [None])[0]
            if inner:
                url = unquote(inner)  # switch to the inner original URL
                parsed = urlparse(url)
        # validate scheme + host
        if parsed.scheme not in {"http", "https"}:
            return Response(status_code=400, content="Bad URL scheme")
        if parsed.netloc not in ALLOWED_IMAGE_HOSTS:
            return Response(status_code=403, content="Host not allowed")
    except Exception:
        return Response(status_code=400, content="Bad URL")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Referer": "https://www.allrecipes.com/",
        "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    }

    timeout = httpx.Timeout(10.0, connect=5.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=headers) as client:
        r = await client.get(url)
        if r.status_code != 200:
            return Response(status_code=r.status_code, content=f"Upstream error {r.status_code}")
        content_type = r.headers.get("Content-Type", "image/jpeg")
        resp = StreamingResponse(r.aiter_bytes(), media_type=content_type)
        resp.headers["Cache-Control"] = "public, max-age=86400"
        return resp


# ----- Search API -----
@app.post("/api/search")
def search(body: SearchBody):
    q = (body.q or "").strip()
    if not q:
        raise HTTPException(400, "q (query) is required")

    # 1) LLM: NL -> SQL
    try:
        sql = nl_to_sql(q, body.limit)
        sql = clean_sql(sql)
    except Exception as e:
        raise HTTPException(400, f"LLM/SQL error: {e}")

    # 2) Execute SQL
    try:
        conn = get_conn()
        cur = conn.execute(sql)
        rows = [dict(row) for row in cur.fetchall()]
    except Exception as e:
        raise HTTPException(400, f"SQL execution error: {e}")
    finally:
        try:
            conn.close()
        except Exception:
            pass

    # 3) Enrich: if image missing but id present, fetch images in one query
    if rows and ("image" not in rows[0]) and ("id" in rows[0]):
        ids = tuple(r["id"] for r in rows)
        # Build a valid IN clause for single/multiple ids
        ids_clause = f"({ids[0]})" if len(ids) == 1 else str(ids)
        conn2 = get_conn()
        cur2 = conn2.execute(f"SELECT id, image FROM recipes WHERE id IN {ids_clause}")
        id_to_image = {row["id"]: row["image"] for row in cur2.fetchall()}
        conn2.close()
        for r in rows:
            r["image"] = id_to_image.get(r["id"])

    # 4) Post-process: expand ingredients preview nicely
    for r in rows:
        if "ingredients_json" in r and r["ingredients_json"]:
            try:
                items = json.loads(r["ingredients_json"])
                r["ingredients_preview"] = items[:8]
            except Exception:
                r["ingredients_preview"] = []

    return {"sql": sql, "count": len(rows), "results": rows}
