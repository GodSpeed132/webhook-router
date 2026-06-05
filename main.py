from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def read_root():
    return {"Hello":"World"}



nameList = {"first":'james', 
            "second":'john',
            "third": 'doe'}

@app.get("/test")
async def test():
    return nameList

@app.post("/test/try/add")
async def add_name(data : dict):
    nameList.update(data)
    return nameList




@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}

