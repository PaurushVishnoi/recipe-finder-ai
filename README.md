# 🍲 Recipe Finder AI App

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![SQLite](https://img.shields.io/badge/Database-SQLite-green)](https://www.sqlite.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An **AI-powered Recipe Finder App** that stores recipes in a database and lets you query them using natural language.  
Built with **Python + SQLite**, designed to easily extend into **PostgreSQL + AI embeddings** in the future. 🚀

---

## ⚡ Features
- ✅ Load recipes from a JSON dataset into SQLite  
- ✅ Clean schema with `title`, `ingredients`, `cuisine`, `ratings`, etc.  
- ✅ Fast database setup with `create_db.py`  
- 🔜 Full-text search (FTS5) on titles and ingredients  
- 🔜 Semantic search with embeddings (OpenAI or Hugging Face)  
- 🔜 API (FastAPI) endpoints for `/search` and `/recipes/{id}`  

---

## 🚀 Getting Started

### 1. Clone the repo
```
git clone https://github.com/YOUR_USERNAME/recipe-finder-ai.git
cd recipe-finder-ai
```

### 2. Setup environment
```
pip install -r requirements.txt
```

### 2. Build the database
```
python init_db.py
```

This creates recipes.db from recipes-en.json.