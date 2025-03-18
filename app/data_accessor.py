from datetime import datetime

from dotenv import dotenv_values
from supabase import Client

from app.custom_errors import (
    InvalidFriendship,
    InvalidHangout,
    InvalidUser,
    UnexpectedError,
    InvalidNotificationMessage,
    InvalidNotificationId,
)
from app.custom_types import FriendStatus, HangoutStatus, InviteeStatus
from app.supabase_client import get_supabase_client
from app.utils import send_notification_bulk

config = dotenv_values(".env")


def check_for_friendship(user_A: str, user_B: str):
    """
    A helper function to retrive a row in the friends table.

    NOTE: This function assumes that user_A < user_B.

    So make sure you do this check before passing in the values:

        primary, secondary = (user_A, user_B) if user_A < user_B else (user_B, user_A)

    If the row exist, we will return the row_id, otherwise we will return None.
    """

    supabase: Client = get_supabase_client()

    try:
        response = (
            supabase.table("friends")
            .select()
            .eq("user_A", user_A)
            .eq("user_B", user_B)
            .maybe_single()
            .execute()
        )

        if response:
            return response.data["id"]

    except Exception as e:
        raise UnexpectedError(f"Unexpected error: {str(e)}")


def send_friend_request(user_A: str, user_B: str) -> dict:
    """
    1. Raise errors if user_id or friend_id is falsey
    2. Initialize variables:
        primary = smaller id
        secondary = larger id
    3. Checks for entries in `friends` table
    4. If there are no entries, we will insert a row into the `friends` table
    5. If there are , we will return a message to the caller.
    """

    supabase: Client = get_supabase_client()

    if user_A is None:
        raise InvalidUser("User ID can not null")
    if user_B is None:
        raise InvalidUser("Friend ID can not null")
    if user_A == user_B:
        raise ValueError(
            f"The IDs of the users can not be the same. User A: {user_A}, User B: {user_B}"
        )

    primary, secondary = (user_A, user_B) if user_A < user_B else (user_B, user_A)

    try:
        friendship_id = check_for_friendship(primary, secondary)
        if not friendship_id:
            data = {
                "user_A": primary,
                "user_B": secondary,
                "status": FriendStatus.PENDING,
                "sender": user_A,
            }
            response = supabase.table("friends").insert(data).execute()
            if response.data[0]["id"]:
                return {
                    "status": 200,
                    "message": "Succesfully sent the friend request.",
                }
    except UnexpectedError as e:
        raise e

    return {
        "status": 500,
        "message": "Unable to add friends. Users are already in a friendship.",
    }


def remove_friend(friendship_id: str):
    """
    1. Removing a friend request by deleting the row from the `friends` table
    2. If no rows were updated, we return an error response.
    3. If friendship_id is falsy, we raise an InvalidFriendship error.
    """

    if friendship_id is None or friendship_id == "":
        raise InvalidFriendship("Friendship ID can not null")

    supabase: Client = get_supabase_client()

    try:
        check_response = (
            supabase.table("friends").select().eq("id", friendship_id).execute()
        )

        if len(check_response.data) == 0:
            return {"error": 500, "message": "Friendship does not exist"}

        response = supabase.table("friends").delete().eq("id", friendship_id).execute()

        if response.data[0]["id"] == friendship_id:
            return {"status": 200, "message": "Succesfully removed the friendship."}

    except Exception as e:
        raise UnexpectedError(f"Unexpected error: {str(e)}")


def get_notifications(user_id: str):
    """
    Retrieve all notifications for a given user.

    1. Raise an error if `user_id` is falsy.
    2. Query the `notifications` table to fetch notifications for the user.
    3. For each notification, if there's a sender, retrieve sender username & profile_img
    3. Return the list of notifications.

    If an error occurs, raise an UnexpectedError.
    """

    if not user_id:
        raise InvalidUser("User ID cannot be null")

    supabase: Client = get_supabase_client()

    try:
        response = (
            supabase.table("notifications")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )

        notifications = response.data if response.data else []

        for notif in notifications:
            notif["users"] = (
                get_user_info(notif["sender"])
                if notif["sender"]
                else {"username": "Unknown", "profile_img": None}
            )

        return {"status": 200, "notifications": notifications}

    except Exception as e:
        raise UnexpectedError(f"Unexpected error: {str(e)}")


def get_user_info(user_id: str) -> dict:
    """
    Retrieves username and profile_img for a given user

    1. Raise an error if user_id is null / falsey
    2. Query supabase for user with user_id, to retrieve username and profile_img
    3. Return response.data if not falsey, else return default dictionary
    """

    if not user_id:
        raise InvalidUser("User ID cannot be null")

    supabase: Client = get_supabase_client()
    try:
        response = (
            supabase.from_("users")
            .select("username, profile_img")
            .eq("auth_id", user_id)
            .single()
            .execute()
        )

        return (
            response.data
            if response.data
            else {"username": "Unknown", "profile_img": None}
        )
    except Exception as e:
        raise UnexpectedError(f"Unexpected error: {str(e)}")


def update_notification(notification_id: str, message: str) -> dict:
    """
    Updates a notification message and type

    1. Raises errors if 'notification_id' or 'message" is falsy
    2. Updates the row with message and a type of general
    3. Returns a status code of success else 404 error
    """

    if not notification_id:
        raise InvalidNotificationId("Notification ID cannot be null")
    if not message:
        raise InvalidNotificationMessage("Notification message cannot be null")

    supabase: Client = get_supabase_client()

    try:
        response = (
            supabase.table("notifications")
            .update({"message": message, "type": "general"})
            .eq("id", notification_id)
            .execute()
        )

        return (
            {"status": 200, "message": "Notification updated successfully"}
            if response.data
            else {
                "status": 500,
                "message": "Something went wrong with updating notification",
            }
        )

    except Exception as e:
        raise UnexpectedError(f"Unexpected error: {str(e)}")


def remove_notification(notification_id: str, user_id: str) -> dict:
    """
    Attempts to delete a notification directly.

    1. Raise errors if `notification_id` or `user_id` is falsy.
    2. Perform the delete operation.
    3. If no records were deleted, return a 404 Not Found response.
    """

    if not notification_id:
        raise ValueError("Notification ID cannot be null")
    if not user_id:
        raise ValueError("User ID cannot be null")

    supabase: Client = get_supabase_client()

    try:
        response = (
            supabase.table("notifications")
            .delete()
            .eq("id", notification_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not response.data:
            return {
                "status": 404,
                "message": "Notification not found or does not belong to user",
            }

        return {"status": 200, "message": "Notification successfully removed"}

    except Exception as e:
        raise UnexpectedError(f"Unexpected error: {str(e)}")


def fetch_friends(uuid: str) -> dict:
    """
    1. Checks if uuid is empty, raised an InvalidUser if so.
    2. Checks if user exist in user table.
        a. We are doing this because if we query "friends" and the uuid does not exist, it will return an empty list. This will help with debugging.
    2. Fetchs all rows where uuid = user_A or uuid = user_b.
    3. We will always return `response.data` because if there are no results found from the query, `response.data` will be an empty list.
    """

    supabase: Client = get_supabase_client()

    if uuid is None:
        raise InvalidUser("User ID can not null")

    try:
        user_exist = (
            supabase.table("users")
            .select("auth_id")
            .eq("auth_id", uuid)
            .maybe_single()
            .execute()
        )

        if not user_exist.data:
            return {"status": 404, "message": "User does not exist."}

        response = (
            supabase.table("friends")
            .select("id", "user_A", "user_B", "status", "created_at")
            .or_(f"user_A.eq.{uuid},user_B.eq.{uuid}")
            .execute()
        )

        response = supabase.rpc(
            "fetch_friends",
            {
                "currentuser": uuid,
            },
        ).execute()

        return {"status": 200, "friends": response.data}

    except UnexpectedError as e:
        raise e


def friends_autocomplete(uuid: str, query: str) -> dict:
    """
    A function to look for partial matches when searching for friends.

    1. If uuid is falsy we raise an error. If the query is empty, we return nothing.
    2. We will call a procedure that we created.

    Note: when calling this function on the frontend, make sure to throttle or debounce to prevent spam request.

    Links to procedure:
        SQL Query: https://supabase.com/dashboard/project/iseoomsaaenxnrmceksg/api?rpc=friends_autocomplete
        Docs: https://supabase.com/dashboard/project/iseoomsaaenxnrmceksg/sql/83099a29-8e38-402f-bb4a-c535dd0d2b29
    """

    supabase: Client = get_supabase_client()

    if uuid is None:
        raise InvalidUser("User ID can not null")

    try:
        response = supabase.rpc(
            "friends_autocomplete",
            {
                "currentuser": uuid,
                "name": query,
            },
        ).execute()

        if not response.data:
            return {"suggestions": []}

        return {
            "suggestions": [
                {
                    "uuid": friend["id"],
                    "email": friend["email"],
                    "username": friend["username"],
                }
                for friend in response.data
                if friend["id"] != uuid
            ]
        }

    except UnexpectedError as e:
        raise e


def new_hangout(
    creator_username: str,
    creator_id: str,
    invitee_ids: list[str],
    title: str,
    date_range_start: str,
    date_range_end: str,
) -> dict:
    """
    1. Raise errors if:
        a. creator_username or creator_id or title are falsey.
        b. invitee_ids is empty.
        a. date_range_end <= date_range_start.
    2. Create new hangout object in the hangouts table.
    3. Invite people to the hangout.
    """
    if creator_username == "":
        raise ValueError("Creator username can not be empty")

    if creator_id is None or creator_id == "":
        raise InvalidUser("Creator ID can not null")

    if len(invitee_ids) == 0:
        raise InvalidUser("Invitee IDs can not be empty")

    if title == "":
        raise ValueError("Title can not be empty")

    start = datetime.fromisoformat(date_range_start)
    end = datetime.fromisoformat(date_range_end)
    if end <= start:
        raise ValueError("End date can not be before start date")

    supabase: Client = get_supabase_client()

    data = {
        "creator_id": creator_id,
        "invitee_ids": invitee_ids,
        "title": title,
        "date_range_start": date_range_start,
        "date_range_end": date_range_end,
        "status": HangoutStatus.INVITES_SENT,
    }

    try:
        response = supabase.table("hangouts").insert(data).execute()
        if response.data[0]["id"]:
            invite_users(
                creator_id, creator_username, response.data[0]["id"], invitee_ids
            )
            return {"status": 200, "message": "Succesfully created the hangout."}
    except Exception as e:
        raise UnexpectedError(f"Unexpected error: {str(e)}")


def invite_users(
    creator_id: str, creator_username: str, hangout_id: str, invitee_ids: list[str]
) -> dict:
    """
    1. Raise errors if hangout_id is falsey.
    2. For each invitee:
        a. Insert a new row in the hangout_participants table.
        b. Send a notification to the invitee.
    """

    if hangout_id is None or hangout_id == "":
        raise InvalidHangout("Hangout ID can not null")

    supabase: Client = get_supabase_client()

    data = [
        {
            "hangout_id": hangout_id,
            "user_id": invitee_id,
            "status": InviteeStatus.PENDING,
        }
        for invitee_id in invitee_ids
    ]

    try:
        response = supabase.table("hangout_participants").insert(data).execute()
        notifResponse = send_notification_bulk(
            creator_id,
            invitee_ids,
            f"{creator_username} has invited you to a hangout",
            "hangout-invite",
            hangout_id,
        )
        if response.data and notifResponse["status"] == 200:
            return {
                "status": 200,
                "message": "Succesfully invited users to the hangout.",
            }
    except Exception as e:
        raise UnexpectedError(f"Unexpected error: {str(e)}")


def respond_to_invite(hangout_id: str, user_id: str, status: InviteeStatus) -> dict:
    """
    1. Raise errors if hangout_id or user_id is falsey.
    2. Raise errors if hangout_participants row does not exist.
    3. Update the status of the hangout_participants row to incoming status.
    """

    if hangout_id is None or hangout_id == "":
        raise InvalidHangout("Hangout ID can not null")

    supabase: Client = get_supabase_client()

    try:
        response = (
            supabase.table("hangout_participants")
            .update({"status": status})
            .eq("hangout_id", hangout_id)
            .eq("user_id", user_id)
            .execute()
        )

        if response.data:
            check_for_pending(hangout_id)
            return {"status": 200, "message": "Succesfully updated the invite."}
        return {"status": 404, "message": "Hangout invite not found."}
    except Exception as e:
        raise UnexpectedError(f"Unexpected error: {str(e)}")


def check_for_pending(hangout_id: str):
    """
    1. Raise errors if hangout_id is falsey.
    2. Check if there are any pending invites for the hangout.
    3. If there are no pending invites, update the status of the hangout to "fetching-availability".
    """

    if hangout_id is None or hangout_id == "":
        raise InvalidHangout("Hangout ID can not null")

    supabase: Client = get_supabase_client()

    try:
        response = (
            supabase.table("hangout_participants")
            .select()
            .eq("hangout_id", hangout_id)
            .eq("status", InviteeStatus.PENDING)
            .execute()
        )

        if not response.data:
            supabase.table("hangouts").update(
                {"status": HangoutStatus.FETCHING_AVAILABILITY}
            ).eq("id", hangout_id).execute()
    except Exception as e:
        raise UnexpectedError(f"Unexpected error: {str(e)}")


def get_hangout_participants(hangout_id: str):
    """WIP"""

    if hangout_id is None or hangout_id == "":
        raise InvalidHangout("Hangout ID can not null")

    supabase: Client = get_supabase_client()

    try:
        response = (
            supabase.table("hangout_participants").select().eq("hangout_id", hangout_id)
        )
        print(response.data)
    except Exception as e:
        raise UnexpectedError(f"Unexpected error: {str(e)}")


def get_hangouts(user_id: str):
    """
    Retrieve all hangouts for a given user.

    1. Raise an error if `user_id` is falsy.
    2. Query the `hangouts` table to fetch hangouts where the user is the creator or an invitee.
    3. Return the list of hangouts ordered by `scheduled_time`.
    """

    if not user_id:
        raise InvalidUser("User ID cannot be null")

    supabase: Client = get_supabase_client()

    try:
        response = (
            supabase.table("hangouts")
            .select()
            .or_(f"creator_id.eq.{user_id},invitee_ids.cs.{{{user_id}}}")
            .order("scheduled_time", desc=False)
            .execute()
        )

        if response.data:
            return {"status": 200, "hangouts": response.data}
        return {"status": 200, "hangouts": []}

    except Exception as e:
        raise UnexpectedError(f"Unexpected error: {str(e)}")


def accept_friendship(friendship_id: str):
    """
    1. Accepting a friend request by changing status from pending to accepted.
    2. If no rows were updated, we return an error response.
    3. If friendship_id is falsy, we raise an InvalidFriendship error.
    4. If users are already friends, we return an error response.
    """

    if friendship_id is None or friendship_id == "":
        raise InvalidFriendship("Friendship ID can not null")

    supabase: Client = get_supabase_client()

    try:
        check_response = (
            supabase.table("friends").select().eq("id", friendship_id).execute()
        )

        if len(check_response.data) == 0:
            return {"error": 500, "message": "Friendship does not exist"}

        if check_response.data[0]["status"] == FriendStatus.ACCEPTED:
            return {"error": 500, "message": "Users are already friends"}

        response = (
            supabase.table("friends")
            .update({"status": FriendStatus.ACCEPTED})
            .eq("id", friendship_id)
            .execute()
        )

        return {"status": 200, "message": "Succesfully accepted the friend request."}

    except Exception as e:
        raise UnexpectedError(f"Unexpected error: {str(e)}")
