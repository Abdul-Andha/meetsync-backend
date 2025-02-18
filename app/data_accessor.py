from supabase import Client, create_client
from dotenv import dotenv_values

config = dotenv_values(".env")
supabase_url = config["SUPABASE_URL"]
supabase_key = config["SUPABASE_KEY"]
supabase: Client = create_client(supabase_url, supabase_key)


class InvalidUser(Exception):
    """User ID can not be null"""


def check_for_friendship(user_A: str, user_B: str):
    """
    A helper function to retrive a row in the friends table.
    
    If the row exist, we will return the row_id, otherwise we will return None.
    """
    response_1 = (
        supabase.table("friends")
        .select()
        .eq("user_A", user_A)
        .eq("user_B", user_B).maybe_single()
        .execute()
    )
    response_2 = (
        supabase.table("friends")
        .select()
        .eq("user_A", user_B)
        .eq("user_B", user_A).maybe_single()
        .execute()
    )

    if response_1:
        return response_1.data["id"]

    if response_2:
        return response_2.data["id"]
    
    return None


def add_new_friend(user_id: str, friend_id: str) -> str:
    """
    1. Raise errors if user_id or friend_id is falsey
    2. Check for entries in `friends` table
        Relations bidirectional, for example (A,B) or (B,A) so we query for both.
    3. If there are no entries, we will insert a row into the `friends` table
    4. If there are , we will return a message to the caller.      
    """

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
        if response.data[0]['id']:
            return "Succesfully created the friendship."
    
    return "Unable to add friends. Users are already in a friendship."
    

def remove_friend(user_id: str, friend_id: str) -> str:
    """
    1. Raise errors if user_id or friend_id is falsey
    2. Check for entries in `friends` table
        Relations bidirectional, for example (A,B) or (B,A) so we query for both.
    3. If there are no entries, we will return a message to the caller.
    4. If there are , we will delete the row
    """
        
    if user_id is None:
        raise InvalidUser("User ID can not null")
    if friend_id is None:
        raise InvalidUser("Friend ID can not null")

    friendship_id = check_for_friendship(user_id, friend_id)

    if friendship_id is None:
        return "Unable to remove friends. Users are not in a friendship."
    
    response = supabase.table("friends").delete().eq("id", friendship_id).execute()
    if response.data[0]["id"]:
        return "Succesfully removed the friendship"

