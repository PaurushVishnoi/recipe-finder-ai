# 1) Small Python base
FROM python:3.11-slim

# 2) System deps (if you need build tools later, add: build-essential)
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# 3) App files
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code (FastAPI app, scripts, data)
COPY . .

# 4) Build the SQLite DB once at build time (uses scripts/init_db.py from your repo)
# If it ever needs to refresh, rebuild the image.
RUN python scripts/init_db.py || true

# 5) Expose the FastAPI port & run uvicorn on all interfaces
EXPOSE 8000
ENV PORT=8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
