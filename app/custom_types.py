from enum import Enum


class HangoutStatus(str, Enum):
    INVITES_SENT = "invites_sent"
    FETCHING_AVAILABILITY = "fetching-availability"
    DETERMINING_LOCATION = "determining-location"
    CONFIRM_TIME = 'confirm-time'
    CONFIRM_MEETUP = 'confirm-meetup'
    CONFIRM = 'confirmed'
    DECLINED = 'declined'


class InviteeStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"


class FriendStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"

class NotificationType(str, Enum):
    HANGOUT_INVITE = 'hangout-invite'
    FRIEND_REQUEST = 'friend-request'
    GENERAL = 'general'
    SELECT_AVAILABILITY = 'select-availability'
    SELECT_PLACRES = 'select-places'
    CONFIRM_MEETUP = 'confirm-meetup'
    CONFIRM_TIME = 'confirm-time'