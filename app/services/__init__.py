"""Business Logic Layer.

Services raise ServiceError with a user-safe message; the Presentation Layer
turns that into a flash message. Services never import Flask request objects.
"""


class ServiceError(Exception):
    """A rule was violated; the message is safe to show to the user."""


class ConflictError(ServiceError):
    """The action clashes with current state (e.g. slot already taken)."""
