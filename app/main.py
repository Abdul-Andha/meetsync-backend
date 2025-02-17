import uvicorn
import os
from fastapi import FastAPI
from dotenv import dotenv_values

config = dotenv_values(".env")
app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


if __name__ == "__main__":
    IS_PROD = config["IS_PROD"] == "True"
    if IS_PROD:
        print("Deploying to Prod")
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=443,
            ssl_keyfile="/certs/privkey.pem",
            ssl_certfile="/certs/fullchain.pem",
        )
    else:
        print("Deploying to Dev")
        uvicorn.run(app, host="0.0.0.0", port=8000)
