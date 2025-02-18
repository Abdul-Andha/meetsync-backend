import os

from dotenv import dotenv_values
from supabase import Client
from supabase_client import get_supabase_client

config = dotenv_values(".env")


class InvalidUser(Exception):
    """User ID can not be null"""


def check_for_friendship(user_A: str, user_B: str):
    """
    A helper function to retrive a row in the friends table.

    If the row exist, we will return the row_id, otherwise we will return None.
    """

    supabase : Client = get_supabase_client()

    response_1 = (
        supabase.table("friends")
        .select()
        .eq("user_A", user_A)
        .eq("user_B", user_B)
        .maybe_single()
        .execute()
    )
    response_2 = (
        supabase.table("friends")
        .select()
        .eq("user_A", user_B)
        .eq("user_B", user_A)
        .maybe_single()
        .execute()
    )

    if response_1:
        return response_1.data["id"]

    if response_2:
        return response_2.data["id"]

    return None


def add_new_friend(user_id: str, friend_id: str) -> dict:
    """
    1. Raise errors if user_id or friend_id is falsey
    2. Check for entries in `friends` table
        Relations bidirectional, for example (A,B) or (B,A) so we query for both.
    3. If there are no entries, we will insert a row into the `friends` table
    4. If there are , we will return a message to the caller.
    """

    supabase : Client = get_supabase_client()

    if user_id is None:
        raise InvalidUser("User ID can not null")
    if friend_id is None:
        raise InvalidUser("Friend ID can not null")

    friendship_id = check_for_friendship(user_id, friend_id)

    if not friendship_id:
        data = {
            "user_A": user_id,
            "user_B": friend_id,
        }
        response = supabase.table("friends").insert(data).execute()
        if response.data[0]["id"]:
            return { "status":  200 ,"message": "Succesfully created the friendship."}

    return { "status":  500 ,"message": "Unable to add friends. Users are already in a friendship."}


def remove_friend(user_id: str, friend_id: str) -> dict:
    """
    1. Raise errors if user_id or friend_id is falsey
    2. Check for entries in `friends` table
        Relations bidirectional, for example (A,B) or (B,A) so we query for both.
    3. If there are no entries, we will return a message to the caller.
    4. If there are , we will delete the row
    """

    supabase : Client = get_supabase_client()

    if user_id is None:
        raise InvalidUser("User ID can not null")
    if friend_id is None:
        raise InvalidUser("Friend ID can not null")

    friendship_id = check_for_friendship(user_id, friend_id)

    if friendship_id is None:
        return { "status": 500 ,"message": "Unable to remove friends. Users are not in a friendship."}

    response = supabase.table("friends").delete().eq("id", friendship_id).execute()
    if response.data[0]["id"]:
        return { "status": 200 ,"message": "Succesfully removed the friendship"}
