from enum import Enum


class HangoutStatus(str, Enum):
    INVITES_SENT = "invites_sent"
    FETCHING_AVAILABILITY = "fetching-availability"
    DETERMINING_LOCATION = "determining-location"
    CONFIRM_TIME = "confirm-time"
    CONFIRM_MEETUP = "confirm-meetup"
    CONFIRM = "confirmed"


class InviteeStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"


class FlowStatus(str, Enum):
    PENDING_TIME_INPUT = "pending-time-input"
    SUBMITTED_TIME_INPUT = "submitted-time-input"
    PENDING_TIME_VOTE = "pending-time-vote"
    SUBMITTED_TIME_VOTE = "submitted-time-vote"
    PENDING_LOCATION_VOTE = "pending-location-vote"
    SUBMITTED_LOCATION_VOTE = "submitted-location-vote"
    PENDING_CONFIRM_TIME = "pending-confirm-time"
    SUBMITTED_CONFIRM_TIME = "submitted-confirm-time"
    PENDING_CONFIRM_LOCATION = "pending-confirm-location"
    SUBMITTED_CONFIRM_LOCATION = "submitted-confirm-location"


class FriendStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"


class NotificationType(str, Enum):
    HANGOUT_INVITE = "hangout-invite"
    FRIEND_REQUEST = "friend-request"
    GENERAL = "general"
    SELECT_AVAILABILITY = "select-availability"
    SELECT_PLACRES = "select-places"
    CONFIRM_MEETUP = "confirm-meetup"
    CONFIRM_TIME = "confirm-time"
