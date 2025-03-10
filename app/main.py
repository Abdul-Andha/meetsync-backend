from dotenv import dotenv_values
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import app.data_accessor as da
from app.custom_errors import InvalidUser, UnexpectedError, InvalidHangout
from app.custom_types import InviteeStatus

config = dotenv_values(".env")
app = FastAPI()
origins = [
    "http://localhost:3000",
    "https://www.meet-sync.us",
    "https://meet-sync.us",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,  # Allows cookies and authorization headers
    allow_methods=["*"],  # Allows all HTTP methods
)


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


class HangoutRequest(BaseModel):
    creator_username: str
    creator_id: str
    invitee_ids: list[str]
    title: str
    date_range_start: str
    date_range_end: str


class HangoutResponseRequest(BaseModel):
    hangout_id: str
    user_id: str


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
async def process_friends_autocomplete(
    authenticated_user_uuid: str, query: str
) -> dict:
    uuid = authenticated_user_uuid
    query = query
    try:
        response = da.friends_autocomplete(uuid, query)
        return response
    except InvalidUser as e:
        return {"status": 400, "message": str(e)}
    except ValueError as e:
        return {"status": 400, "message": str(e)}


@app.post("/new-hangout")
async def process_new_hangout(request: HangoutRequest) -> dict:
    creator_username = request.creator_username
    creator_id = request.creator_id
    invitee_ids = request.invitee_ids
    title = request.title
    date_range_start = request.date_range_start
    date_range_end = request.date_range_end

    try:
        response = da.new_hangout(
            creator_username,
            creator_id,
            invitee_ids,
            title,
            date_range_start,
            date_range_end,
        )
        return response
    except InvalidUser as e:
        return {"status": 400, "message": str(e)}
    except Exception as e:
        return {"status": 500, "message": str(e)}


@app.post("/accept-invite")
async def process_accept_invite(request: HangoutResponseRequest) -> dict:
    hangout_id = request.hangout_id
    user_id = request.user_id

    try:
        response = da.respond_to_invite(hangout_id, user_id, InviteeStatus.ACCEPTED)
        return response
    except InvalidUser as e:
        return {"status": 400, "message": str(e)}
    except InvalidHangout as e:
        return {"status": 400, "message": str(e)}
    except Exception as e:
        return {"status": 500, "message": str(e)}


@app.post("/decline-invite")
async def process_decline_invite(request: HangoutResponseRequest) -> dict:
    hangout_id = request.hangout_id
    user_id = request.user_id

    try:
        response = da.respond_to_invite(hangout_id, user_id, InviteeStatus.DECLINED)
        return response
    except InvalidUser as e:
        return {"status": 400, "message": str(e)}
    except InvalidHangout as e:
        return {"status": 400, "message": str(e)}
    except Exception as e:
        return {"status": 500, "message": str(e)}
