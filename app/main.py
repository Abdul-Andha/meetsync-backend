import uvicorn
import os
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


if __name__ == "__main__":
    ENV = os.getenv("ENV", "dev")

    if ENV == "prod":
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=443,
            ssl_keyfile="/etc/letsencrypt/live/api.meet-sync.us/privkey.pem",
            ssl_certfile="/etc/letsencrypt/live/api.meet-sync.us/fullchain.pem",
        )
    else:
        uvicorn.run(app, host="0.0.0.0", port=8000)
