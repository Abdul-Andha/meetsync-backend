import os

from dotenv import dotenv_values
from supabase import Client

from app.custom_errors import InvalidUser, UnexpectedError
from supabase_client import get_supabase_client

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


def add_new_friend(user_A: str, user_B: str) -> dict:
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
            }
            response = supabase.table("friends").insert(data).execute()
            if response.data[0]["id"]:
                return {"status": 200, "message": "Succesfully created the friendship."}
    except UnexpectedError as e:
        raise e

    return {
        "status": 500,
        "message": "Unable to add friends. Users are already in a friendship.",
    }


def remove_friend(user_A: str, user_B: str) -> dict:
    """
    1. Raise errors if user_id or friend_id is falsey
    2. Initialize variables:
        primary = smaller id
        secondary = larger id
    3. Checks for entries in `friends` table
    4. If there are no entries, we will return a message to the caller.
    5. If there are , we will delete the row
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
    except UnexpectedError as e:
        raise e

    if friendship_id is None:
        return {
            "status": 500,
            "message": "Unable to remove friends. Users are not in a friendship.",
        }

    response = supabase.table("friends").delete().eq("id", friendship_id).execute()
    if response.data[0]["id"]:
        return {"status": 200, "message": "Succesfully removed the friendship"}
    

def get_notifications(user_id: str):
    """
    Retrieve all notifications for a given user.

    1. Raise an error if `user_id` is falsy.
    2. Query the `notifications` table to fetch notifications for the user.
    3. Return the list of notifications.

    If an error occurs, raise an UnexpectedError.
    """

    if not user_id:
        raise InvalidUser("User ID cannot be null")

    supabase: Client = get_supabase_client()

    try:
        response = (
            supabase.table("notifications")
            .select()
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )

        if response.data:
            return {"status": 200, "notifications": response.data}
        return {"status": 200, "notifications": response.data}

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
            return {"status": 404, "message": "Notification not found or does not belong to user"}

        return {"status": 200, "message": "Notification successfully removed"}

    except Exception as e:
        raise UnexpectedError(f"Unexpected error: {str(e)}")
    

def fetch_friends(uuid: str) -> dict:
    """
   

    """

    supabase: Client = get_supabase_client()

    if uuid is None:
        raise InvalidUser("User ID can not null")

    try:
        response = (
            supabase.table("friends")
            .select("*")
            .or_(f"user_A.eq.{uuid},user_B.eq.{uuid}")
            .execute()
        )
    except UnexpectedError as e:
        raise e

    return {"res" : response}

    if response.data[0]["id"]:
        return {"status": 200, "message": "Succesfully removed the friendship"}