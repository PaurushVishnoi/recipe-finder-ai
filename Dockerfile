FROM python:3.12-slim
WORKDIR /app
ENV PIP_NO_CACHE_DIR=1
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
# OPTIONAL: build demo DB into the image; comment out if you prefer runtime init
# RUN python scripts/init_db.py || true
ENV PORT=8000
EXPOSE 8000
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]