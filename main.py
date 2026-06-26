from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from enum import Enum
import psycopg2
import os
from dotenv import load_dotenv
import json
import hmac
import hashlib


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
db = psycopg2.connect(DATABASE_URL, sslmode ='require')
app = FastAPI()


@app.post("/webhook/github")
async def github(request: Request):

    payload = await request.json()
    current_event = request.headers.get('x-github-event')
    print(request.headers)

    header = request.headers.get('x-hub-signature-256')
    body = await request.body()
    known_secret = b'jamestesting'
    my_signature = hmac.new(known_secret, body, hashlib.sha256).hexdigest()
    git_signature = header.removeprefix("sha256=")


    if hmac.compare_digest(my_signature, git_signature):
        cursor = db.cursor()
        cursor.execute(
            'INSERT INTO events (source, event_type, payload) VALUES (%s, %s, %s)', 
            ('github', current_event, json.dumps(payload))
            )
        db.commit()
        cursor.close()

        return {'status': 'recived'}
    else:
        raise HTTPException(status_code=401, detail='Unauthorized')
    


class model(BaseModel):
    temp =[]


@app.post("/create_rules/slack")
async def create_rules(shape: model):
    cursor = db.cursor()
    cursor.execute('')

        







