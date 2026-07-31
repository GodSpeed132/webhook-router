# GitHub Webhook Router

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.116+-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1?logo=postgresql&logoColor=white)
![GitHub Webhooks](https://img.shields.io/badge/GitHub-Webhooks-181717?logo=github&logoColor=white)
![asyncpg](https://img.shields.io/badge/asyncpg-Connection%20Pooling-336791)
![APScheduler](https://img.shields.io/badge/APScheduler-Background%20Jobs-2E8B57)
![HTTPX](https://img.shields.io/badge/HTTPX-Async%20HTTP-8A2BE2)

A backend service built with **FastAPI** that receives GitHub webhook events, verifies their authenticity using **HMAC SHA-256**, stores them in PostgreSQL, and routes them to configurable destinations. Failed deliveries are automatically retried using **APScheduler** with an exponential backoff strategy.

---

# Features

- Receive GitHub webhook events through FastAPI
- Verify incoming webhook signatures using HMAC SHA-256
- Store webhook events in PostgreSQL
- Configure routing rules for different GitHub event types
- Forward events to external webhook endpoints (Discord, Slack, etc.)
- Retry failed deliveries automatically using APScheduler
- Exponential backoff retry strategy
- Asynchronous PostgreSQL access using asyncpg connection pooling
- Shared application resources managed through FastAPI's lifespan events

---

# Architecture

```text
                GitHub
                   │
                   ▼
        POST /webhook/github
                   │
                   ▼
        Verify HMAC Signature
                   │
                   ▼
          Store Event in DB
                   │
                   ▼
      Lookup Routing Rule
                   │
                   ▼
      Forward to Destination
             │
     ┌───────┴────────┐
     ▼                ▼
 Success           Failure
                      │
                      ▼
        Store Failed Delivery
                      │
                      ▼
         APScheduler Retry Job
                      │
                      ▼
         Exponential Backoff
```

---

# Tech Stack

## Backend

- Python
- FastAPI
- asyncpg
- HTTPX
- APScheduler

## Database

- PostgreSQL
- Supabase

## Validation

- Pydantic

## Security

- HMAC SHA-256 Webhook Verification

---

# API Endpoints

| Method | Endpoint | Description |
|---------|----------|-------------|
| POST | `/webhook/github` | Receive GitHub webhook events |
| POST | `/create_rules` | Create a routing rule |
| GET | `/get_rules` | Retrieve routing rules |

---

# Running Locally

## Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/webhook-router.git

cd webhook-router
```

---

## Create a virtual environment

```bash
python -m venv .venv
```

### macOS / Linux

```bash
source .venv/bin/activate
```

### Windows

```powershell
.venv\Scripts\activate
```

---

## Install dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file in the project root.

```env
DATABASE_URL=your_postgresql_connection_string
```

---

## Run the application

```bash
uvicorn main:app --reload
```

The API will be available at

```
http://127.0.0.1:8000
```

---

# Example Flow

1. GitHub sends a webhook.
2. FastAPI receives the request.
3. The webhook signature is verified.
4. The event is stored in PostgreSQL.
5. A routing rule is retrieved.
6. The webhook payload is formatted.
7. The formatted message is sent to the configured destination.
8. Failed deliveries are stored for retry.
9. APScheduler retries failed deliveries using exponential backoff.

---

# Design Decisions

## FastAPI Lifespan

The PostgreSQL connection pool is created during application startup using FastAPI's lifespan events and stored in `app.state.pool`. This allows all request handlers and scheduled background jobs to safely share the same pool throughout the application's lifetime.

## Connection Pooling

The application uses **asyncpg** connection pooling instead of opening a new PostgreSQL connection for every request. Connections are acquired only while interacting with the database and are immediately returned to the pool afterward.

## Background Retry System

Failed webhook deliveries are stored in the database instead of being retried immediately. APScheduler periodically checks for pending deliveries and retries them using exponential backoff to avoid repeatedly sending requests to unavailable endpoints.

## Webhook Security

Incoming GitHub webhooks are verified using GitHub's HMAC SHA-256 signature before any processing occurs. Requests with invalid signatures are rejected with a `401 Unauthorized` response.

---

# Future Improvements

- Authentication for managing routing rules
- Support for additional webhook providers
- Multiple destination integrations (Slack, Microsoft Teams, etc.)
- Docker support
- Unit and integration tests
- Structured logging
- Metrics and monitoring
- Railway deployment

---

# What I Learned

This project gave me practical experience with:

- Building asynchronous backend services using FastAPI
- Managing PostgreSQL connection pools with asyncpg
- FastAPI application lifecycle and shared application state
- GitHub webhook authentication using HMAC SHA-256
- Background scheduling with APScheduler
- Retry strategies using exponential backoff
- Designing resilient backend systems that can recover from temporary delivery failures