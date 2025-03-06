from app.custom_errors import InvalidUser, UnexpectedError
from supabase_client import get_supabase_client

def send_notification(sender: str | None, receiver: str, msg: str, noti_type: str):
    """
    A helper function to send notification to a user

    Sender is the person who is requesting something from receiver such as invitations 
    Receiver will get notification information associated with their id

    Check if receiver is falsey
    Sender and receiver cannot be the same since you're not sending things to yourself
    If needed you can keep sender blank 
    Insert parameter information to the table
    """
    supabase: Client = get_supabase_client()

    if receiver is None:
        raise InvalidUser("Receiver cannot be null")
    if sender == receiver:
        raise ValueError(
            f"The IDs of the users can not be the same. Sender: {sender}, Receiver: {receiver}"
        )

    try:
        response = (
            supabase.table("notifications")
            .insert({"user_id": receiver, "sender": sender, "message": msg, "type": noti_type})
            .execute()
        )

        if response.data[0]['id']:
            return {"status": 200, "message": "Succesfully sent notification."}
    except Exception as e:
        raise UnexpectedError(f"Unexpected error: {str(e)}")

