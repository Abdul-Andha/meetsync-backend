from datetime import datetime

from dotenv import dotenv_values
from supabase import Client

from app.algo import findRecommendations

from app.custom_errors import (
    InvalidFriendship,
    InvalidHangout,
    InvalidUser,
    UnexpectedError,
    InvalidNotificationMessage,
    InvalidNotificationId,
)
from app.custom_types import (
    FriendStatus,
    HangoutStatus,
    InviteeStatus,
    FlowStatus,
    NotificationType,
)
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
) -> dict:
    """
    1. Raise errors if:
        a. creator_username or creator_id or title are falsey.
        b. invitee_ids is empty.
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

    supabase: Client = get_supabase_client()

    data = {
        "creator_id": creator_id,
        "invitee_ids": invitee_ids,
        "title": title,
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
    data.append(
        {
            "hangout_id": hangout_id,
            "user_id": creator_id,
            "status": InviteeStatus.ACCEPTED,
            "flowStatus": FlowStatus.PENDING_TIME_INPUT,
        }
    )

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
    flowStaus = None
    if status == InviteeStatus.ACCEPTED:
        flowStatus = FlowStatus.PENDING_TIME_VOTE

    try:
        response = (
            supabase.table("hangout_participants")
            .update({"status": status, "flowStatus": flowStatus})
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


def get_user_hangouts(user_id: str):
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


def create_poll(hangout_id: str, options: list[str]):
    """
    Creates a poll for a hangout

    1. If there was more than 5 options passed in, we raise a ValueError
    2. If hangout_id is falsey we raise a value error
    3. Check if a poll is already created, if so, we return an error
    4. Insert all poll options for a hangout
    5. Get hangout information and send notification to all invitees
    6. If all is good, we return a 200
    """

    unique_options = set(options)
    if len(unique_options) > 5:
        raise ValueError("Options exceeds limit. You can only pass in 5 options")
    if hangout_id is None or hangout_id == "":
        raise InvalidHangout("Hangout ID can not null")

    supabase: Client = get_supabase_client()

    try:
        data = []
        for option in unique_options:
            day, start_time, end_time = option.split(",")
            insertData = {
                "hangout_id": hangout_id,
                "selected_day": day,
                "start_time": start_time,
                "end_time": end_time,
            }
            data.append(insertData)

        check_response = (
            supabase.table("meetup_options")
            .select("hangout_id")
            .eq("hangout_id", hangout_id)
            .execute()
        )
        if len(check_response.data) > 0:
            return {
                "status": 500,
                "message": "Unable to create poll. A poll for the hangout already exist.",
            }

        response = supabase.table("meetup_options").insert(data).execute()

        if response.data:
            hangout_response = get_hangout(hangout_id)
            if hangout_response["status"] != 200:
                return {
                    "status": 200,
                    "message": "Succesfully created poll but unable to retrieve hangout information and send notifications.",
                }
            hangout_info = hangout_response["hangout"]

            notifResponse = send_notification_bulk(
                hangout_info["creator_id"],
                hangout_info["invitee_ids"],
                f'Availability phase initiated for {hangout_info["title"]}',
                NotificationType.SELECT_AVAILABILITY,
                hangout_id,
            )
            if notifResponse["status"] != 200:
                return {
                    "status": 200,
                    "message": "Succesfully created poll but unable to send notifications to all invitees.",
                }

            status_response = (
                supabase.table("hangout_participants")
                .update({"flowStatus": FlowStatus.SUBMITTED_TIME_INPUT})
                .eq("user_id", hangout_info["creator_id"])
                .eq("hangout_id", hangout_id)
                .execute()
            )
            if not status_response.data:
                return {
                    "status": 500,
                    "message": "Succesfully created poll and sent notifications but unable to update your status.",
                }

            return {
                "status": 200,
                "message": "Succesfully created poll and added your options.",
            }
    except Exception as e:
        raise UnexpectedError(f"Unexpected error: {str(e)}")


def get_poll(hangout_id: str):
    """
    Gets all the poll options for a hangout

    1. If hangout_id is falsey we raise a value error
    2. Query meetup_options to get the options for a hangout
    3. If all is good, we return a 200 with the options
    """

    if hangout_id is None or hangout_id == "":
        raise InvalidHangout("Hangout ID can not null")

    supabase: Client = get_supabase_client()
    try:
        response = (
            supabase.table("meetup_options")
            .select("id, start_time, end_time, selected_day")
            .eq("hangout_id", hangout_id)
            .execute()
        )
        if response.data:
            data = [
                {
                    "id": option["id"],
                    "option": option["selected_day"]
                    + ","
                    + option["start_time"]
                    + ","
                    + option["end_time"],
                }
                for option in response.data
            ]
            return {"status": 200, "options": data}
        return {"status": 200, "options": []}

    except Exception as e:
        raise UnexpectedError(f"Unexpected error: {str(e)}")


def vote(hangout_id: int, option_ids: list[str], user_id: str):
    """
    Submits a vote for a hangout

    1. If hangout_id, option_id or user_id is falsey we raise an error
    2. We then get the vote options and make sure the option the user is trying to vote for is an actual selection from the poll
        2a. If is not, we raise an error
        2b. Otherwise we submit the vote
    3. After we submit the vote:
        3a. Update this user's status in hangout_participants table to "submitted-time-vote"
        3b. We get all the participants in an hangout, and all the votes and check if theyre equal
            - If they are equal that means everyone has voted.
            - We know this is true because `user_id` and `hangout_id` are a composite key in `meetup_votes` table so there will never be duplicate votes from the same user
    4. If everyone vote, we call a helper function to get the winner and update the hangouts table. The col we are updating is `scheduled_time`
    """

    if not hangout_id:
        raise InvalidHangout("Hangout ID can not null")

    if not user_id:
        raise InvalidUser("User ID cannot be null")

    if not option_ids or len(option_ids) == 0:
        raise ValueError("Options cannot be empty")

    supabase: Client = get_supabase_client()

    try:

        concluded = check_if_vote_is_concluded(supabase, hangout_id)

        if concluded:
            return {
                "status": 500,
                "message": "No longer accepting votes for hangout. Poll is concluded.",
            }

        data = [
            {"user_id": user_id, "option_id": option_id, "hangout_id": hangout_id}
            for option_id in option_ids
        ]

        vote_options = (
            supabase.table("meetup_options")
            .select("id")
            .eq("hangout_id", hangout_id)
            .execute()
        )

        flattened_options = [option["id"] for option in vote_options.data]
        for option_id in flattened_options:
            if option_id not in flattened_options:
                return {
                    "status": 500,
                    "message": "Invalid voting option: " + option_id,
                }

        vote_response = supabase.table("meetup_votes").upsert(data).execute()

        if vote_response.data:
            status_response = (
                supabase.table("hangout_participants")
                .update({"flowStatus": FlowStatus.SUBMITTED_TIME_VOTE})
                .eq("user_id", user_id)
                .eq("hangout_id", hangout_id)
                .execute()
            )

            if not status_response.data:
                return {
                    "status": 500,
                    "message": "Successfully added vote but unable to update your status.",
                }

            hangout_response = get_hangout(hangout_id)

            invitees = hangout_response["hangout"]["invitee_ids"]
            creator_id = hangout_response["hangout"]["creator_id"]
            title = hangout_response["hangout"]["title"]

            user_votes = (
                supabase.table("meetup_votes")
                .select("user_id")
                .eq("hangout_id", hangout_id)
                .execute()
            )

            flattend_user_votes = [user["user_id"] for user in user_votes.data]
            unique_users = set(flattend_user_votes)

            if len(unique_users) == len(invitees):  # change this clause
                update_hangout_response = set_scheduled_time(
                    supabase, hangout_id, invitees, creator_id, title
                )
                if not update_hangout_response:
                    return {
                        "status": 500,
                        "message": "Successfully added vote. We tried to conclude the vote since you are the final memeber to vote but there was an error while updating the hangout.",
                    }
            return {
                "status": 200,
                "message": "Succesfully added your vote",
            }

    except Exception as e:
        raise UnexpectedError(f"Unexpected error: {str(e)}")


def set_scheduled_time(
    supabase: Client, hangout_id: int, invitees: list[str], creator_id: str, title: str
):
    """
    A helper function to set the winning time for a vote, send notifs, and update statuses

    1. Get the winner view sql query : https://supabase.com/dashboard/project/iseoomsaaenxnrmceksg/sql/04256748
    2. Update hangouts table with the value returned from the query
    """
    winning_time_repsponse = supabase.rpc(
        "get_vote_winner",
        {
            "input_hangout_id": hangout_id,
        },
    ).execute()

    winning_date = winning_time_repsponse.data[0]["selected_day"]
    winning_start_time = winning_time_repsponse.data[0]["start_time"]
    winning_end_time = winning_time_repsponse.data[0]["end_time"]
    updated_hangout_response = (
        supabase.table("hangouts")
        .update(
            {
                "scheduled_date": winning_date,
                "scheduled_start_time": winning_start_time,
                "scheduled_end_time": winning_end_time,
                "scheduled_time": str(winning_date) + " " + str(winning_start_time),
                "status": HangoutStatus.CONFIRM_TIME,
            }
        )
        .eq("id", hangout_id)
        .execute()
    )

    updated_participants_response = (
        supabase.table("hangout_participants")
        .update({"flowStatus": FlowStatus.PENDING_CONFIRM_TIME})
        .eq("hangout_id", hangout_id)
        .execute()
    )

    notifResponse = send_notification_bulk(
        creator_id,
        invitees,
        f"Meetup time has been chosen and set for {title} at {winning_start_time} on {winning_date}",
        NotificationType.CONFIRM_TIME,
        hangout_id,
    )

    return (
        len(updated_hangout_response.data) == 1
    )  # len is 1 if the update was succesful


def check_if_vote_is_concluded(supabase: Client, hangout_id: int):
    """
    A helper function to check if a poll is not concluded

    Note: `scheduled_time` is either NULL or a datetimestamp

    1. Fetches `scheduled_time` val from row.
    2. If `scheduled_time` is not null, return true. This means theres a date timestamp
    3. Otherwise return false, this means the value is None
    """

    hangout = (
        supabase.table("hangouts")
        .select("scheduled_time")
        .eq("id", hangout_id)
        .execute()
    )
    return hangout.data[0]["scheduled_time"] is not None


def get_hangout(hangout_id: str):
    """
    Retrieve hangout object from supabase given hangout_id

    1. Raise error if hangout_id is falsey.
    2. Query supabase for hangout row
    """

    if hangout_id is None or hangout_id == "":
        raise InvalidHangout("Hangout ID can not null")

    supabase: Client = get_supabase_client()

    try:
        response = (
            supabase.table("hangouts")
            .select()
            .eq("id", hangout_id)
            .maybe_single()
            .execute()
        )

        if response and response.data:
            return {"status": 200, "hangout": response.data}
        return {"status": 200, "hangout": None}

    except Exception as e:
        raise UnexpectedError(f"Unexpected error: {str(e)}")


def get_hangout_participants(hangout_id: str):
    """
    Retrieve all active participants in specified hangout

    1. Raise error if hangout_id is falsey.
    2. Query supabase for participants in hangout that have accepted
    3. Return queried results or [] if none found
    """

    if hangout_id is None or hangout_id == "":
        raise InvalidHangout("Hangout ID can not null")

    supabase: Client = get_supabase_client()

    try:
        response = (
            supabase.table("hangout_participants")
            .select("*, user:users(username)")
            .eq("hangout_id", hangout_id)
            .eq("status", "accepted")
            .execute()
        )

        if response.data:
            return {"status": 200, "participants": response.data}
        return {"status": 200, "participants": []}

    except Exception as e:
        raise UnexpectedError(f"Unexpected error: {str(e)}")


def push_recommendations(hangout_id: str, places):
    """
    Push recommended places to supabase recommendations table

    1. Raise error if hangout_id is falsey.
    2. Add each place to the recommendations table
    3. Return success message
    """

    if hangout_id is None or hangout_id == "":
        raise InvalidHangout("Hangout ID can not null")

    supabase: Client = get_supabase_client()

    data = [
        {
            "hangout_id": hangout_id,
            "name": place["displayName"]["text"],
            "address": place["formattedAddress"],
            "location": place["location"],
        }
        for place in places
    ]

    try:
        response = supabase.table("place_recommendations").insert(data).execute()

        if response.data:
            return {
                "status": 200,
                "message": "Succesfully added recommendations.",
            }
    except Exception as e:
        raise UnexpectedError(f"Unexpected error: {str(e)}")


def get_recommendations(hangout_id: str):
    """
    Get recommended places from supabase recommendations table for given hangout

    1. Raise error if hangout_id is falsey
    2. Raise error if hangout does not exist
    3. Query supabase for recommendations
        3a. Return 404 if none found. This should not happen because algo should run first
        3b. Return recommendations
    """

    if hangout_id is None or hangout_id == "":
        raise InvalidHangout("Hangout ID can not null")

    supabase: Client = get_supabase_client()

    try:
        response = get_hangout(hangout_id)
        if not response["hangout"]:
            raise InvalidHangout("Hangout does not exist.")

        response = (
            supabase.table("place_recommendations")
            .select()
            .eq("hangout_id", hangout_id)
            .execute()
        )

        if response.data:
            return {"status": 200, "recommendations": response.data}
        return {"status": 404, "message": "No recommendations found for hangout."}

    except InvalidHangout as e:
        raise e
    except Exception as e:
        raise UnexpectedError(f"Unexpected error: {str(e)}")


def fetch_hangouts(uuid: str, name: str = "") -> dict:
    """
    1. Checks if uuid is empty, raises InvalidUser if so.
    2. Checks if user exists in users table.
    3. Calls the `fetch_user_hangouts` RPC with uuid + optional name query.
    4. Always returns `response.data`.
    Stored procedure link: https://supabase.com/dashboard/project/iseoomsaaenxnrmceksg/api?rpc=fetch_user_hangouts
    """
    supabase: Client = get_supabase_client()

    if uuid is None:
        raise InvalidUser("User ID cannot be null")

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

        response = supabase.rpc(
            "fetch_user_hangouts",
            {
                "currentuser": uuid,
                "name": name or "",
            },
        ).execute()

        for hangout in response.data:
            hangout["participants"] = get_hangout_participants(hangout["id"])[
                "participants"
            ]

        return {"status": 200, "hangouts": response.data}

    except UnexpectedError as e:
        raise e


def cancel_hangout(hangout_id: int):
    """
    A helper function to delete a hangout.

    1. If hangout_id is falsy, we raise an InvalidHangout error
    2. Otherwise, we will delete the row from the hangouts table

    As long as all foreign keys are set to cascade on delete, all related rows referencing the `hangout_id` will also be automatically removed.
    """

    if hangout_id is None:
        raise InvalidHangout("Hangout ID can not null")

    supabase: Client = get_supabase_client()

    try:
        response = supabase.table("hangouts").delete().eq("id", hangout_id).execute()

        if len(response.data) == 0:
            return {
                "status": 500,
                "message": "Unable to delete hangout. Make sure you are passing in a vaid hangout id",
            }

        return {"status": 200, "message": "Succesfully deleted the hangout."}
    except UnexpectedError as e:
        raise e


def submit_batch_votes(user_id: str, votes: list[dict]) -> dict:
    """
    Efficiently submits multiple ranked votes via upsert.
    """
    supabase: Client = get_supabase_client()

    try:
        if not user_id or not votes:
            return {"status": 400, "message": "Missing user or votes."}

        user_check = (
            supabase.table("users")
            .select("auth_id")
            .eq("auth_id", user_id)
            .maybe_single()
            .execute()
        )
        if not user_check.data:
            return {"status": 404, "message": "User not found."}

        formatted_votes = [
            {
                "user_id": user_id,
                "recommendation_id": vote["recommendation_id"],
                "rank": vote["rank"],
            }
            for vote in votes
        ]

        supabase.table("recommendation_votes").upsert(
            formatted_votes, on_conflict="user_id, recommendation_id"
        ).execute()

        return {"status": 200, "message": "Votes submitted successfully"}

    except Exception as e:
        return {"status": 500, "message": str(e)}


def submit_time_confirmation(
    hangout_id: str, user_id: str, address: str, transport: str, travel_time: str
):
    """
    Confirm a user for submitting meetup time.

    1. check hangout_id and user_id are not null
    2. Check if other necessary details are not null
    3. check if user is a valid user
    4. update user information based on request body (in hangout_participants)
    5. check if all hangout_participants part of hangout_id confirmed their meetup time
    6. if all confirmed:
       - update hangout status to "determining-location"
       - start algorithm
    """

    if hangout_id is None or not hangout_id:
        raise InvalidHangout("Hangout ID can not null")
    if user_id is None or not user_id:
        raise InvalidUser("User ID cannot be null")

    errorMsgStr = ""
    if not address:
        errorMsgStr += "Address not found "
    if not transport:
        errorMsgStr += "Transport not found "
    if not travel_time:
        errorMsgStr += "Travel Time not found"
    if errorMsgStr:
        return {"status": 400, "message": errorMsgStr}

    supabase: Client = get_supabase_client()

    try:
        user_check = (
            supabase.table("users")
            .select("auth_id")
            .eq("auth_id", user_id)
            .maybe_single()
            .execute()
        )

        if not user_check.data:
            return {"status": 404, "message": "User not found."}

        response = (
            supabase.table("hangout_participants")
            .update(
                {
                    "flowStatus": FlowStatus.SUBMITTED_CONFIRM_TIME,
                    "start_address": address,
                    "transport": transport,
                    "travel_time": travel_time,
                }
            )
            .eq("hangout_id", hangout_id)
            .eq("user_id", user_id)
            .execute()
        )
        if response.data:
            if check_all_submitted(hangout_id, "submitted-confirm-time"):
                change_hangout_status = (
                    supabase.table("hangouts")
                    .update({"status": HangoutStatus.DETERMINING_LOCATION})
                    .eq("id", hangout_id)
                    .execute()
                )
                start_algo(hangout_id)
                return {
                    "status": 200,
                    "message": "Successfully confirmed participant and started algorithm",
                }
            return {
                "status": 200,
                "message": "Successfully confirmed participant and updated meetup time information",
            }

    except Exception as e:
        raise UnexpectedError(f"Unexpected error: {str(e)}")


def start_algo(hangout_id: str):
    """
    helper function to start algorithm for finding recommendations, updating status, and sending notifications to all users

    1. start findRecommendations algorithm
    2. Retrieve information
       - creator_id and title from get_hangout
       - all hangout_participants
    3. update status for all hangout participants to 'confirm-location'
    4. send notification to all hangout_participants
    """
    findRecommendations(hangout_id)

    supabase: Client = get_supabase_client()

    hangout_response = get_hangout(hangout_id)

    creator_id = hangout_response["hangout"]["creator_id"]
    title = hangout_response["hangout"]["title"]

    hangout_participants = (
        supabase.table("hangout_participants")
        .select()
        .eq("hangout_id", hangout_id)
        .eq("status", "accepted")
        .execute()
    )

    updated_participants_response = (
        supabase.table("hangout_participants")
        .update({"flowStatus": FlowStatus.PENDING_LOCATION_VOTE})
        .eq("hangout_id", hangout_id)
        .execute()
    )

    notifResponse = send_notification_bulk(
        creator_id,
        [participant["user_id"] for participant in hangout_participants.data],
        f"Pick your location soon for {title}",
        NotificationType.SELECT_PLACES,
        hangout_id,
    )


def check_all_submitted(hangout_id: str, flowStatus: str) -> bool:
    """
    helper function to check if all participants have a particular status
    *typically used for checking if all users confirmed something like meetup time

    1. Retrieve data
       - get all hangout participants
       - get all hangout participants with flowStatus (any arbitrary status)
    2. Compare length and return boolean value
    """
    supabase: Client = get_supabase_client()
    try:
        hangout_participants = (
            supabase.table("hangout_participants")
            .select()
            .eq("hangout_id", hangout_id)
            .eq("status", "accepted")
            .execute()
        )
        participants_submitted = (
            supabase.table("hangout_participants")
            .select()
            .eq("hangout_id", hangout_id)
            .eq("flowStatus", flowStatus)
            .execute()
        )
        if hangout_participants.data and participants_submitted.data:
            return len(hangout_participants.data) == len(participants_submitted.data)
        return False
    except Exception as e:
        raise UnexpectedError(f"Unexpected error: {str(e)}")


def submit_time_decline(hangout_id: str, user_id: str):
    """
    Decline user for submitting meetup time
    (aka remove user from hangout)

    1. check hangout_id and user_id are not null
    2. check if user is a valid user
    3. delete user from hangout
    """

    if hangout_id is None or not hangout_id:
        raise InvalidHangout("Hangout ID can not null")
    if user_id is None or not user_id:
        raise InvalidUser("User ID cannot be null")

    supabase: Client = get_supabase_client()
    try:
        user_check = (
            supabase.table("users")
            .select("auth_id")
            .eq("auth_id", user_id)
            .maybe_single()
            .execute()
        )

        if not user_check.data:
            return {"status": 404, "message": "User not found."}

        response = (
            supabase.table("hangout_participants")
            .delete()
            .eq("hangout_id", hangout_id)
            .eq("user_id", user_id)
            .execute()
        )

        if response.data:
            return {
                "status": 200,
                "message": "Successfully declined participant and updated status",
            }
    except Exception as e:
        raise UnexpectedError(f"Unexpected error: {str(e)}")


def update_flow_status(user_id, new_status: str, hangout_id):
    if user_id is None:
        raise InvalidUser("User ID can not be null")
    if hangout_id is None:
        raise InvalidHangout("Hangout ID can not be null")
    if new_status is None:
        raise ValueError("Status can not be empty.")

    supabase: Client = get_supabase_client()

    try:

        if new_status == "declined":
            # delete row and return
            delete_response = (
                supabase.table("hangout_participants")
                .delete()
                .eq("user_id", user_id)
                .eq("hangout_id", hangout_id)
                .execute()
            )
            if len(delete_response.data) == 0:
                return {"status": 500, "message": "Error while updating flow status."}

            return {
                "status": 200,
                "message": "Successfully declined final confirmation.",
            }
        else:
            data = {
                "user_id": user_id,
                "flowStatus": (FlowStatus.ACCEPTED_FINAL_CONFIRMATION),
            }
        response = (
            supabase.table("hangout_participants")
            .update(data)
            .eq("user_id", user_id)
            .eq("hangout_id", hangout_id)
            .execute()
        )
        if len(response.data) == 0:
            return {"status": 500, "message": "Error while updating flow status."}

        return {"status": 200, "message": "Successfully accepted final confirmation."}
    except Exception as e:
        return {"status": 500, "message": str(e)}
