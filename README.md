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
- ✅ Fast database setup with `init_db.py`
- ✅ API (FastAPI) endpoints for `/search`
- 🔜 Semantic search with embeddings (OpenAI or Hugging Face)  

---

## System Design

![System Design Diagram](docs/Sequence_diagram.png)

##  Prerequisites

- Python 3.9–3.13 installed
- An OpenAI account and API key (for the Text-to-SQL demo)
- (Recommended) Git and a terminal

### 🔐 OpenAI API Key

Create an API key from your OpenAI dashboard.
```
Login to Open AI -> https://platform.openai.com/settings/profile/api-keys

Click "+ Create a new secret key" -> Name your key for e.g.:- "My demo key" -> Copy the generated key 

This key will be used to be pasted in .env file
```
In the project root, create a .env file and this one line **( Just replace "sk-your-key-here" with your generated key , just paste it as it is no need to use "")**:
```
OPENAI_API_KEY=sk-your-key-here
```
Tip: Never commit your key. .env is git-ignored.

## 🚀 Getting Started

### 1. Clone the repo
```
git clone https://github.com/PaurushVishnoi/recipe-finder-ai.git
cd recipe-finder-ai
```

### 2. Setup environment
```
pip install -r requirements.txt
```

### 2. Build the database
```
cd scripts 

python init_db.py
```

This creates recipes.db from recipes-en.json.

### 3. Run the app 

Run the server 
```
python -m uvicorn app.main:app --reload
```

Open the local host ( link ) :-
```
http://127.0.0.1:8000/
```


### 🥳 You are good to cook now! 🔥🍳🥗

---

# AWS Deployment Guide

This repository contains the code and deployment workflow for running **Recipe Finder AI** on **AWS ECS Fargate** with Docker, GitHub Actions, and supporting AWS infrastructure.

The following guide explains the full setup process step by step.

---

## 🚀 Overview
- Dockerized **FastAPI** app running on **ECS Fargate**
- **OpenAI API key** stored securely in **AWS Secrets Manager**
- Application logs sent to **CloudWatch Logs**
- Networking handled by **Application Load Balancer (ALB)**
- **CI/CD pipeline** with GitHub Actions → Amazon ECR → ECS

---

## 📋 Prerequisites
- AWS Account with IAM permissions for **ECS, ECR, IAM, Secrets Manager, and CloudWatch**
- GitHub repository with branch **`pvAWS`**
- Docker installed locally
- OpenAI API key

## Deployment

Switch to the branch pvAWS as are using this branch for CI/CD deployment

```
git checkout pvAWS
```

- [AWS Deployment Guide](./docs/AWS_DEPLOYMENT.md)