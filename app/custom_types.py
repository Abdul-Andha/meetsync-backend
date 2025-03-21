from enum import Enum


class HangoutStatus(str, Enum):
    INVITES_SENT = "invites_sent"
    FETCHING_AVAILABILITY = "fetching-availability"
    DETERMINING_LOCATION = "determining-location"


class InviteeStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"


class FriendStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
