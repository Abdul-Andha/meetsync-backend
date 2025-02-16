import uvicorn
import os
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


if __name__ == "__main__":
    ENV = os.getenv("ENV", "dev")
    PORT = 443 if ENV == "prod" else 8000

    uvicorn.run(app, host="0.0.0.0", port=PORT)
