class InvalidUser(Exception):
    """User ID can not be null"""


class InvalidHangout(Exception):
    """Hangout ID can not be null"""


class InvalidFriendship(Exception):
    """Friendship ID can not be null"""


class UnexpectedError(Exception):
    """Use this class for all unexpected exeptions"""


class InvalidNotificationMessage(Exception):
    """Notification message cannot be null"""


class InvalidNotificationId(Exception):
    """Notification Id cannot be null"""


class ExternalAPIError(Exception):
    """Use this class for all external API errors"""
