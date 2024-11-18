from fastapi import FastAPI
from main.settings import settings

app = FastAPI()


@app.get("/")
async def root():
    print(settings.database_url)
    return {"message": "Hello from loghive"}
