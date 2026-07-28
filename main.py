from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from enum import Enum
import asyncpg
import os
from dotenv import load_dotenv
import json
import hmac
import hashlib
import httpx
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler


load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")



async def retry_request(app: FastAPI):
    async with app.state.pool.acquire() as conn:
        failed_requests = await conn.fetch(
            'SELECT * FROM failed_deliveries WHERE next_retry_at<=$1 AND retry_count < 3', 
            datetime.now(timezone.utc)
            )

        for row in failed_requests:
            async with conn.transaction():
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.post(row['destination'], json={"text": row['formatted_message']})
                        response.raise_for_status()
                        await conn.execute('DELETE FROM failed_deliveries where id=$1', row['id'])

                except Exception as e:
                    print(e)
                    failed_retry_count = row['retry_count']
                    failed_next_retry_at = datetime.now(timezone.utc) + timedelta(minutes=2**failed_retry_count)
                    await conn.execute('UPDATE failed_deliveries set retry_count=$1, next_retry_at=$2 WHERE id=$3', 
                                    failed_retry_count + 1, failed_next_retry_at, row['id'])


scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    
    
    app.state.pool = await asyncpg.create_pool(DATABASE_URL)

    scheduler.add_job(retry_request, "interval", minutes=1, max_instances=1, kwargs={"app":app})

    scheduler.start()

    yield
    await app.state.pool.close()
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)


@app.post("/webhook/github")
async def github(request: Request):
    payload = await request.json()
    current_event = request.headers.get('x-github-event')
    #print(request.headers)

    header = request.headers.get('x-hub-signature-256')
    body = await request.body()
    known_secret = b'jamestesting'
    my_signature = hmac.new(known_secret, body, hashlib.sha256).hexdigest()
    git_signature = header.removeprefix("sha256=")

    if hmac.compare_digest(my_signature, git_signature):

        async with request.app.state.pool.acquire() as conn:
            new_id = await conn.fetchval(
                'INSERT INTO events (source, event_type, payload) VALUES ($1, $2, $3) RETURNING id', 
                'github', current_event, json.dumps(payload)
                )
            
            url = await conn.fetchrow(
                'SELECT destination_config FROM routing_rules WHERE source=$1 AND event_type=$2', 
                'github', current_event)

        if url:
            commit_message, timestamp, author = None, None, None
            destination = url['destination_config']['webhook_url']
            commits = payload.get("commits", [])

            if commits:
                commit = commits[0]
                commit_message = commit['message']
                timestamp = commit['timestamp']
                author = commit['author']['username']

            format_message = (
                f"New event from: Github\n"
                f"Event: {current_event}\n"
                f"Author: {author}\n"
                f"Commit message: {commit_message}\n"
                f"Timestamp: {timestamp}"
            )

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(destination, json={"text":format_message})
                    response.raise_for_status()
                    print(response.status_code)

            except Exception as e:
                print(e)
                retry_count = 0
                next_retry_at = datetime.now(timezone.utc) + timedelta(minutes=1)

                async with request.app.state.pool.acquire() as conn:
                    await conn.execute('INSERT INTO failed_deliveries (event_id, destination, error_message, retry_count, next_retry_at, formatted_message) VALUES ($1, $2, $3, $4, $5, $6)',
                                    new_id, destination, str(e), retry_count, next_retry_at, format_message)

        else:
            return {'status': 'received'} 
            
        return {'status': 'received'}
        
    else:
        raise HTTPException(status_code=401, detail='Unauthorized')
    

class EventType(str, Enum):

    push = 'push'
    pull_request = 'pull_request'
    issues = 'issues'
    star = 'star'


class RoutingRules(BaseModel):

    source: str
    event_type: EventType
    destination_type: str
    destination_config: dict


@app.post("/create_rules")
async def create_rules(request: Request, model: RoutingRules):
    async with request.app.state.pool.acquire() as conn:
        await conn.execute(
            'INSERT INTO routing_rules (source, event_type, destination_type, destination_config) VALUES ($1, $2, $3, $4)', 
            model.source, model.event_type.value, model.destination_type, json.dumps(model.destination_config))
            
    return {'status': 'posted'}


@app.get("/get_rules")
async def get_rules(request: Request, source: str | None = None, event_type: str | None = None):

    async with request.app.state.pool.acquire() as conn:
        if source and event_type:
            rows = await conn.fetch(
                'SELECT * FROM routing_rules WHERE source=$1 AND event_type=$2',
                source, event_type
                )
        else:
            rows = await conn.fetch('SELECT * FROM routing_rules')
    
    result = [
        {"id": row[0], "source": row[1], "event_type": row[2], "destination_type": row[3], "destination_config": row[4]}
        for row in rows
        ]
    return result