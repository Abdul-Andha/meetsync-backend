import uvicorn
from dotenv import dotenv_values
from fastapi import FastAPI
from pydantic import BaseModel

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
        return {"status": 500, "message": str(e)}
    except ValueError as e:
        return {"status": 500, "message": str(e)}
    except Exception as e:
        return {"status": 500, "message": str(e)}



@app.post("/remove-friend")
async def process_remove_friends(request: FriendRequest) -> dict:
    user_A = request.user_A
    user_B = request.user_B
    try:
        response = da.remove_friend(user_A, user_B)
    except InvalidUser as e:
        return {"status": 500, "message": str(e)}
    except ValueError as e:
        return {"status": 500, "message": str(e)}

    return response


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
