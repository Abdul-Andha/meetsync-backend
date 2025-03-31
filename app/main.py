from dotenv import dotenv_values
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import app.data_accessor as da
from app.custom_errors import (
    InvalidHangout,
    InvalidUser,
    UnexpectedError,
    InvalidNotificationId,
    InvalidNotificationMessage,
)
from app.custom_types import InviteeStatus
from app.algo import findRecommendations

config = dotenv_values(".env")
app = FastAPI(debug=True)
origins = [
    "http://localhost:3000",
    "https://www.meet-sync.us",
    "https://meet-sync.us",
    "https://*.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class FriendRequest(BaseModel):
    user_A: str
    user_B: str


class AcceptOrDeclineFriendRequest(BaseModel):
    friendship_id: int


class FetchFriedsRequest(BaseModel):
    uuid: str


class NotificationRequest(BaseModel):
    user_id: str


class UpdateNotificationRequest(BaseModel):
    notification_id: str
    new_message: str


class DeleteNotificationRequest(BaseModel):
    notification_id: str
    user_id: str


class HangoutRequest(BaseModel):
    creator_username: str
    creator_id: str
    invitee_ids: list[str]
    title: str


class HangoutResponseRequest(BaseModel):
    hangout_id: str
    user_id: str


class GetHangoutsRequest(BaseModel):
    user_id: str


class CreatePollRequest(BaseModel):
    hangout_id: int
    options: list[str]

class GetPoll(BaseModel):
    hangout_id: str

class VoteRequest(BaseModel):
    hangout_id: int
    option_id: str
    user_id: str


class AlgoRequest(BaseModel):
    hangout_id: str

class FetchHangoutsRequest(BaseModel):
    uuid: str
    name: str = ""  # Optional search query (can be empty)


class CancelHangoutRequest(BaseModel):
    hangout_id: int

class HangoutInfoRequest(BaseModel):
    hangout_id: int


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/send-friend-request")
async def process_send_friend_request(request: FriendRequest) -> dict:
    user_A = (
        request.user_A
    )  # userA is the sender ( the person who sent the friend request )
    
    user_B = request.user_B
    try:
        response = da.send_friend_request(user_A, user_B)
        return response
    except InvalidUser as e:
        return {"status": 400, "message": str(e)}
    except ValueError as e:
        return {"status": 400, "message": str(e)}
    except Exception as e:
        return {"status": 500, "message": str(e)}


@app.post("/add-friend")
async def process_add_friend(request: AcceptOrDeclineFriendRequest) -> dict:
    friendship_id = request.friendship_id

    try:
        response = da.accept_friendship(friendship_id)
        return response
    except InvalidUser as e:
        return {"status": 400, "message": str(e)}
    except ValueError as e:
        return {"status": 400, "message": str(e)}
    except Exception as e:
        return {"status": 500, "message": str(e)}


@app.post("/remove-friend")
async def process_remove_friends(request: AcceptOrDeclineFriendRequest) -> dict:
    """
    Use this route to decline a friend request and to remove a friend
    """
    friendship_id = request.friendship_id

    try:
        response = da.remove_friend(friendship_id)
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




@app.post("/update-notification")
async def change_notification(request: UpdateNotificationRequest) -> dict:
    notification_id = request.notification_id
    message = request.new_message
    try:
        response = da.update_notification(notification_id, message)
        return response
    except InvalidNotificationId as e:
        return {"status": 400, "message": str(e)}
    except InvalidNotificationMessage as e:
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




@app.post("/get-hangouts")
async def get_hangouts_route(request: GetHangoutsRequest) -> dict:
    user_id = request.user_id
    try:
        response = da.get_user_hangouts(user_id)
        return response
    except InvalidUser as e:
        return {"status": 400, "message": str(e)}
    except UnexpectedError as e:
        return {"status": 500, "message": str(e)}
    except Exception as e:
        return {"status": 500, "message": str(e)}
    
@app.post("/get-hangout-info")
async def get_hangout_info_route(request: HangoutInfoRequest) -> dict:
    hangout_id = request.hangout_id
    try:
        response = da.get_hangout(hangout_id)
        if response['hangout']:
            data = {
                'status': response['status'],
                'hangout_info': {
                    'creator_id': response['hangout']['creator_id'],
                    'title': response['hangout']['title']
                }
            }
            return data
        return response
    except InvalidUser as e:
        return {"status": 400, "message": str(e)}
    except UnexpectedError as e:
        return {"status": 500, "message": str(e)}
    except Exception as e:
        return {"status": 500, "message": str(e)}


@app.post("/new-hangout")
async def process_new_hangout(request: HangoutRequest) -> dict:
    creator_username = request.creator_username
    creator_id = request.creator_id
    invitee_ids = request.invitee_ids
    title = request.title

    try:
        response = da.new_hangout(
            creator_username,
            creator_id,
            invitee_ids,
            title,
        )
        return response
    except InvalidUser as e:
        return {"status": 400, "message": str(e)}
    except Exception as e:
        return {"status": 500, "message": str(e)}


@app.post("/cancel-hangout")
async def process_cancel_hangout(request: CancelHangoutRequest) -> dict:
    hangout_id = request.hangout_id
    try:
        response = da.cancel_hangout(hangout_id)
        return response
    except InvalidHangout as e:
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


@app.post("/create-poll")
async def process_create_poll(request: CreatePollRequest) -> dict:
    hangout_id = request.hangout_id
    options = request.options

    try:
        response = da.create_poll(hangout_id, options)
        return response
    except ValueError as e:
        return {"status": 400, "message": str(e)}
    except InvalidHangout as e:
        return {"status": 400, "message": str(e)}
    except Exception as e:
        return {"status": 500, "message": str(e)}
    
@app.post("/get-poll")
async def access_poll_options(request: GetPoll) -> dict:
    hangout_id = request.hangout_id

    try:
        response = da.get_poll(hangout_id)
        return response
    except InvalidHangout as e:
        return {"status": 400, "message": str(e)}
    except Exception as e:
        return {"status": 500, "message": str(e)}

@app.post("/vote")
async def process_vote(request: VoteRequest) -> dict:
    hangout_id = request.hangout_id
    option_id = request.option_id
    user_id = request.user_id

    try:
        response = da.vote(hangout_id, option_id, user_id)
        return response
    except InvalidUser as e:
        return {"status": 400, "message": str(e)}
    except InvalidHangout as e:
        return {"status": 400, "message": str(e)}
    except InvalidHangout as e:
        return {"status": 400, "message": str(e)}
    except ValueError as e:
        return {"status": 400, "message": str(e)}
    except Exception as e:
        return {"status": 500, "message": str(e)}


# this is a test endpoint. It will not be called by the front end
@app.post("/algo-test")
async def process_algo_test(request: AlgoRequest) -> dict:
    hangout_id = request.hangout_id

    try:
        findRecommendations(hangout_id)
        return True
    except InvalidHangout as e:
        return {"status": 400, "message": str(e)}
    except ValueError as e:
        return {"status": 400, "message": str(e)}
    except Exception as e:
        return {"status": 500, "message": str(e)}


@app.get("/get-recommendations")
async def process_get_recommendations(hangout_id: str) -> dict:
    try:
        response = da.get_recommendations(hangout_id)
        return response
    except InvalidHangout as e:
        return {"status": 400, "message": str(e)}
    except ValueError as e:
        return {"status": 400, "message": str(e)}
    except Exception as e:
        return {"status": 500, "message": str(e)}


@app.post("/fetch-hangouts")
async def process_fetch_hangouts(request: FetchHangoutsRequest) -> dict:
    uuid = request.uuid
    name = request.name
    try:
        response = da.fetch_hangouts(uuid, name)
        return response
    except InvalidUser as e:
        return {"status": 400, "message": str(e)}
    except ValueError as e:
        return {"status": 400, "message": str(e)}
    except Exception as e:
        return {"status": 500, "message": str(e)}
