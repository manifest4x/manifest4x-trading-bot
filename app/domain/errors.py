class DomainError(Exception):
    """Base class for errors the API translates into HTTP responses."""

    retriable = False


class UnauthorizedError(DomainError):
    """The webhook token is missing or wrong."""


class InvalidPayloadError(DomainError):
    """The webhook body cannot be turned into a signal."""


class NotificationDeliveryError(DomainError):
    """A provider failed to deliver a notification."""

    retriable = True

    def __init__(self, provider: str, message: str, status_code: int | None = None) -> None:
        super().__init__(f"{provider}: {message}")
        self.provider = provider
        self.status_code = status_code
