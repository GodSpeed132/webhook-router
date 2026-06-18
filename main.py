from fastapi import FastAPI, Request
from pydantic import BaseModel
from enum import Enum
import psycopg2
import os
from dotenv import load_dotenv
import json


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
db = psycopg2.connect(DATABASE_URL, sslmode ='require')
app = FastAPI()

class EventType(str, Enum):
    push = 'push'
    get = 'get'
    insert = 'insert'
    update = 'update'
    delete = 'delete'

class WebhookEvent(BaseModel):
    source: str
    event_type: EventType
    payload: dict



@app.post("/test/try/add")
async def test(data: WebhookEvent):
    cursor = db.cursor()
    cursor.execute(
        'INSERT INTO events (source, event_type, payload) VALUES (%s, %s, %s)', 
        (data.source, data.event_type.value, json.dumps(data.payload))
        )
    db.commit()
    cursor.close()
    return {"status": "received"}



@app.post("/webhook/github")
async def github(request: Request):
    payload = await request.json()
    print(payload)
    cursor = db.cursor()
    cursor.execute(
        'INSERT INTO events (source, event_type, payload) VALUES (%s, %s, %s)', 
        ('github', 'post', json.dumps(payload))
        )
    db.commit()
    db.close()






