import uvicorn
from dotenv import dotenv_values
from fastapi import FastAPI
from pydantic import BaseModel

import app.data_accessor as da

config = dotenv_values(".env")
app = FastAPI()


class FriendRequest(BaseModel):
    user_id: int
    friend_id: int


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/add-friend")
async def process_add_friends(request: FriendRequest) -> dict:
    user_id = request.user_id
    friend_id = request.friend_id

    response = da.add_new_friend(user_id, friend_id)
    return {"res": response}


@app.post("/remove-friend")
async def process_remove_friends(request: FriendRequest) -> dict:
    user_id = request.user_id
    friend_id = request.friend_id

    response = da.remove_friend(user_id, friend_id)
    return {"res": response}


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
