from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from enum import Enum
import psycopg2
import os
from dotenv import load_dotenv
import json
import hmac
import hashlib
import httpx


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


        cursor.execute(
            'SELECT destination_config FROM routing_rules WHERE source=%s AND event_type=%s', 
            ('github', current_event))
        url = cursor.fetchall()
        cursor.close()
        

        if url:

            commit_message, timestamp, author = None, None, None

            if len(payload['commits']) > 0:
                commit_message = payload['commits'][0]['message']
                timestamp = payload['commits'][0]['timestamp']
                author = payload['commits'][0]['author']['username']
            

            format_message = (
                f"New event from: Github\n"
                f"Event: {current_event}\n"
                f"Author: {author}\n"
                f"Commit message: {commit_message}\n"
                f"Timestamp: {timestamp}"
            )

            async with httpx.AsyncClient() as client:
                response = await client.post(url[0][0]['webhook_url'], json={"text":format_message})
                print(response.status_code)
        else:
            return {'status': 'received'} 



        return {'status': 'recieved'}
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


@app.post("/create_rules/slack")
async def create_rules(model: RoutingRules):
    cursor = db.cursor()
    cursor.execute(
        'INSERT INTO routing_rules (source, event_type, destination_type, destination_config) VALUES (%s, %s, %s, %s)', 
        (model.source, model.event_type.value, model.destination_type, json.dumps(model.destination_config))
        )
    db.commit()
    cursor.close()

    return {'status': 'posted'}
        


@app.get("/get_rules")
async def get_rules(source: str | None = None, event_type: str | None = None):
    cursor = db.cursor()
    if source and event_type:
        cursor.execute(
            'SELECT * FROM routing_rules WHERE source=%s AND event_type=%s',
            (source, event_type)
            )
    else:
        cursor.execute('SELECT * FROM routing_rules')

    
    rows = cursor.fetchall()
    
    result = [
        {"id": row[0], "source": row[1], "event_type": row[2], "destination_type": row[3], "destination_config": row[4]}
        for row in rows
        ]
    cursor.close()
    return result