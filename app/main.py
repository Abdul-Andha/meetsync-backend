import sys

import uvicorn
from dotenv import dotenv_values
from fastapi import FastAPI
from pydantic import BaseModel

import app.data_accessor as da
from app.custom_errors import InvalidUser, UnexpectedError

config = dotenv_values(".env")
app = FastAPI()


class FriendRequest(BaseModel):
    user_A: str
    user_B: str


class FetchFriedsRequest(BaseModel):
    uuid: str


class NotificationRequest(BaseModel):
    user_id: str


class DeleteNotificationRequest(BaseModel):
    notification_id: str
    user_id: str


class FriendsAutocompleteRequest(BaseModel):
    authenticated_user_uuid: str
    name_to_query: str


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


@app.post("/get-notifications")
async def fetch_notifications(request: NotificationRequest) -> dict:
    user_id = request.user_id
    try:
        response = da.get_notifications(user_id)
        return response
    except InvalidUser as e:
        return {"status": 400, "message": str(e)}
    except UnexpectedError as e:
        return {"status": 500, "message": str(e)}
    except Exception as e:
        return {"status": 500, "message": str(e)}


@app.post("/remove-notification")
async def delete_notification(request: DeleteNotificationRequest) -> dict:
    notification_id = request.notification_id
    user_id = request.user_id
    try:
        response = da.remove_notification(notification_id, user_id)
        return response
    except InvalidUser as e:
        return {"status": 400, "message": str(e)}
    except UnexpectedError as e:
        return {"status": 500, "message": str(e)}
    except Exception as e:
        return {"status": 500, "message": str(e)}


@app.post("/fetch-friends")
async def process_fetch_friends(request: FetchFriedsRequest) -> dict:
    uuid = request.uuid
    try:
        response = da.fetch_friends(uuid)
        return response
    except InvalidUser as e:
        return {"status": 400, "message": str(e)}
    except ValueError as e:
        return {"status": 400, "message": str(e)}
    except Exception as e:
        return {"status": 500, "message": str(e)}


@app.get("/friends-autocomplete/")
async def process_friends_autocomplete(request: FriendsAutocompleteRequest) -> dict:
    uuid = request.authenticated_user_uuid
    query = request.name_to_query
    try:
        response = da.friends_autocomplete(uuid, query)
        return response
    except InvalidUser as e:
        return {"status": 400, "message": str(e)}
    except ValueError as e:
        return {"status": 400, "message": str(e)}
    except Exception as e:
        return {"status": 500, "message": str(e)}
