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


@app.post("/webhook/github")
async def github(request: Request):
    payload = await request.json()
    current_event = request.headers.get('x-github-event')
    print(request.headers)
    cursor = db.cursor()
    cursor.execute(
        'INSERT INTO events (source, event_type, payload) VALUES (%s, %s, %s)', 
        ('github', current_event, json.dumps(payload))
        )
    db.commit()
    cursor.close()
    return {'status': 'recived'}







