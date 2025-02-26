import uvicorn
from dotenv import dotenv_values
from fastapi import FastAPI
from pydantic import BaseModel
import sys

import app.data_accessor as da
from app.custom_errors import InvalidUser, UnexpectedError

config = dotenv_values(".env")
app = FastAPI()


class FriendRequest(BaseModel):
    user_A: int
    user_B: int


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/add-friend")
async def process_add_friends(request: FriendRequest) -> dict:
    user_A = request.user_A
    user_B = request.user_B
    try:
        response = da.add_new_friend(user_A, user_B)
        return response
    except InvalidUser as e:
        return {"status": 400, "message": str(e)}
    except ValueError as e:
        return {"status": 400, "message": str(e)}
    except Exception as e:
        return {"status": 500, "message": str(e)}


@app.post("/remove-friend")
async def process_remove_friends(request: FriendRequest) -> dict:
    user_A = request.user_A
    user_B = request.user_B
    try:
        response = da.remove_friend(user_A, user_B)
        return response
    except InvalidUser as e:
        return {"status": 400, "message": str(e)}
    except ValueError as e:
        return {"status": 400, "message": str(e)}
    except Exception as e:
        return {"status": 500, "message": str(e)}
