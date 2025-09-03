# Recipe Finder AI – AWS Deployment

This repository contains the **Recipe Finder AI** application and infrastructure configuration for deploying to **AWS ECS Fargate** using **Docker**, **Amazon ECR**, **GitHub Actions**, and supporting AWS services.

---

## 📖 Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Deployment Steps](#deployment-steps)
  - [Step 1 — Add Dockerfile & .dockerignore](#step-1--add-dockerfile--dockerignore)
  - [Step 2 — Create ECR Repository](#step-2--create-ecr-repository)
  - [Step 3 — Store OpenAI API Key in Secrets Manager](#step-3--store-openai-api-key-in-secrets-manager)
  - [Step 4 — Create CloudWatch Logs Group](#step-4--create-cloudwatch-logs-group)
  - [Step 5 — Networking (Security Groups & ALB)](#step-5--networking-security-groups--alb)
  - [Step 6 — ECS Task Execution Role](#step-6--ecs-task-execution-role)
  - [Step 7 — ECS Cluster](#step-7--ecs-cluster)
  - [Step 8 — GitHub OIDC Deploy Role](#step-8--github-oidc-deploy-role)
  - [Step 9 — GitHub Actions Workflow](#step-9--github-actions-workflow)
  - [Step 10 — ECS Task Definition](#step-10--ecs-task-definition)
  - [Step 11 — ECS Service](#step-11--ecs-service)
- [Verification](#verification)
- [Notes](#notes)

---

## 🚀 Overview
- **FastAPI** app served via **Uvicorn**
- Dockerized & deployed to **AWS ECS Fargate**
- Uses **AWS Secrets Manager** for API keys
- Logs sent to **AWS CloudWatch Logs**
- CI/CD pipeline with **GitHub Actions** deploying to ECS
- Public access via **Application Load Balancer**

---

## 📋 Prerequisites
- AWS Account with IAM permissions for ECS, ECR, IAM, Secrets Manager, CloudWatch
- GitHub repository with branch `pvAWS`
- Docker installed locally
- OpenAI API key

---

## 🛠 Deployment Steps

### Step 1 — Add Dockerfile & .dockerignore
Create the following files in your repo (`pvAWS` branch) in the root folder:

**Dockerfile**
```dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python scripts/init_db.py || true
EXPOSE 8000
ENV PORT=8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```
**.dockerignore**

### Step 2 — Create ECR Repository
- Console → **ECR → Create repository**
- Name: `recipe-finder-ai-aws`
- Visibility: **Private**
- Copy URI:

```bash
ACCOUNT_ID.dkr.ecr.eu-central-1.amazonaws.com/recipe-finder-ai-aws
```

### Step 3 — Store OpenAI API Key in Secrets Manager
- Console → **Secrets Manager → Store a new secret**
- Secret type: **Other type of secret**
- Options:
  - **Key/Value**:  
    - Key = `OPENAI_API_KEY`  
    - Value = `sk-...`
  - **Plaintext**: just your key value
- Name: `OpenAIKeyNew`  
- Leave defaults → Store

---

### Step 4 — Create CloudWatch Logs Group
- Console → **CloudWatch → Logs → Log groups → Create**
- Name: `/ecs/recipe`
- Retention: **30 days** (or as preferred)

---

### Step 5 — Networking (Security Groups & ALB)

#### 5a — Security Groups
- VPC → **Security groups → Create security group**

**alb-sg-recipe**
- Inbound: HTTP 80 from `0.0.0.0/0` and `::/0`
- Outbound: allow all (default)

**svc-sg-recipe**
- Inbound: TCP 8000 from security group `alb-sg-recipe`
- Outbound: allow all (default)

#### 5b — Application Load Balancer + Target Group
- EC2 → **Load Balancers → Create → Application Load Balancer**
  - Name: `alb-recipe`
  - Scheme: Internet-facing
  - VPC: default
  - Subnets: choose 2+ public subnets
  - Security group: `alb-sg-recipe`
  - Listener: HTTP :80

- **Target Group**
  - Create target group  
  - Target type: **IP**
  - Name: `tg-recipe`
  - Protocol: HTTP, Port: 8000
  - Health check: Path `/docs`, Success codes `200–399`

Attach target group `tg-recipe` to ALB listener → Create.

---

### Step 6 — ECS Task Execution Role
- IAM → **Roles → Create role**
- Trusted entity: **Elastic Container Service → Elastic Container Service Task**
- Permissions: `AmazonECSTaskExecutionRolePolicy`
- Name: `ecsTaskExecutionRole-recipe`
- Create

---

### Step 7 — ECS Cluster
- ECS → **Clusters → Create cluster**
- Name: `cluster-recipe`
- Create

---

### Step 8 — GitHub OIDC Deploy Role

#### 8a — Create the Role
- IAM → **Roles → Create role**
- Trusted entity type: **Web identity**
- Identity provider: `token.actions.githubusercontent.com`
- Audience: `sts.amazonaws.com`
- Role name: `GitHubActionsDeployRole`

**Trust Policy** (replace `ACCOUNT_ID` and repo info):
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Federated": "arn:aws:iam::ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
    },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {
        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
      },
      "StringLike": {
        "token.actions.githubusercontent.com:sub": "repo:PaurushVishnoi/recipe-finder-ai:ref:refs/heads/pvAWS"
      }
    }
  }]
}
```

**Permissions Policy** (replace ACCOUNT_ID and region):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ECRLogin",
      "Effect": "Allow",
      "Action": ["ecr:GetAuthorizationToken"],
      "Resource": "*"
    },
    {
      "Sid": "ECRPushPull",
      "Effect": "Allow",
      "Action": [
        "ecr:BatchCheckLayerAvailability","ecr:CompleteLayerUpload","ecr:InitiateLayerUpload",
        "ecr:PutImage","ecr:UploadLayerPart","ecr:DescribeRepositories","ecr:BatchGetImage"
      ],
      "Resource": "arn:aws:ecr:eu-central-1:ACCOUNT_ID:repository/recipe-finder-ai-aws"
    },
    {
      "Sid": "ECSRollout",
      "Effect": "Allow",
      "Action": ["ecs:UpdateService","ecs:DescribeServices"],
      "Resource": "*"
    }
  ]
}
```

### Step 9 — GitHub Actions Workflow
- In your repo, create file: `.github/workflows/deploy.yml`
- Contents:

```yaml
name: Build & Deploy to ECS (pvAWS)
on:
  push:
    branches: [ pvAWS ]

permissions:
  id-token: write
  contents: read

env:
  AWS_REGION: eu-central-1
  ECR_REPO: recipe-finder-ai-aws
  CLUSTER: cluster-recipe
  SERVICE: svc-recipe
  IMAGE_TAG: latest

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-region: ${{ env.AWS_REGION }}
          role-to-assume: arn:aws:iam::ACCOUNT_ID:role/GitHubActionsDeployRole

      - name: Login to ECR
        id: ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build image
        run: docker build -t $ECR_REPO:$IMAGE_TAG .

      - name: Tag & push to ECR
        run: |
          ECR_URI=${{ steps.ecr.outputs.registry }}/${{ env.ECR_REPO }}
          docker tag $ECR_REPO:$IMAGE_TAG $ECR_URI:$IMAGE_TAG
          docker push $ECR_URI:$IMAGE_TAG

      - name: Force new ECS deployment
        run: |
          aws ecs update-service \
            --cluster $CLUSTER \
            --service $SERVICE \
            --force-new-deployment
```
- Replace ACCOUNT_ID in the workflow before committing
- Commit & push to branch pvAWS

### Step 10 — Create the ECS Task Definition
- Console → **ECS → Task definitions → Create**
- Launch type: **Fargate**
- **Family**: `task-recipe`
- **OS/Arch**: `Linux/x86_64`
- **Task size**: `0.5 vCPU`, `1–2 GB RAM` (start with `1 GB`)
- **Task execution role**: `ecsTaskExecutionRole-recipe`

**Container → Add container**
- **Name**: `app`
- **Image**:
```bash
ACCOUNT_ID.dkr.ecr.eu-central-1.amazonaws.com/recipe-finder-ai-aws:latest
```
- Port mappings: 8000/tcp

**Environment → Secrets**
- **Name**: `OPENAI_API_KEY`
- **ValueFrom**: Secrets Manager → select `OpenAIKeyNew`
  - If stored as key/value JSON → pick the exact key  
  - If plaintext → select the secret itself  

**Logging**
- **Log driver**: `awslogs`
- **Log group**: `/ecs/recipe`
- **Region**: `eu-central-1`
- **Stream prefix**: `ecs`

- Click **Create**

### Step 11 — Create the ECS Service (wire to ALB)

- Console → **ECS → Clusters → `cluster-recipe` → Create → Service**
- **Compute**: Fargate
- **Application type**: Service
- **Task definition**: `task-recipe:1`
- **Service name**: `svc-recipe`
- **Desired tasks**: `1`
- **Deployment options**: Rolling update (defaults OK)

**Networking**
- **VPC**: default  
- **Subnets**: the public subnets used for the ALB  
- **Auto-assign public IP**: **ENABLED**  
- **Security group**: `svc-sg-recipe`

**Load balancing**
- **Type**: Application Load Balancer  
- **ALB**: `alb-recipe`  
- **Listener**: `HTTP :80`  
- **Target group**: `tg-recipe` (port `8000`)  
- **Health check grace period**: `60 seconds`

- Click **Create service**  
- Wait until the task is **Running** and target group shows **Healthy**

**Open the app**
```bash
http://<alb-dns-name>
```
For e.g. :- 
```
http://alb-recipe-4******9.eu-central-1.elb.amazonaws.com
```
Note : This is just a demo link and not going to work as the service is on pause ( AWS charges for running web app services )

🎉 You are now enjoying the live app!