"""A Pydantic Model representing authentication details for a system under test."""

from pydantic import BaseModel


class AuthModel(BaseModel):
    """A Pydantic Model representing authentication details for a system under test.

    Attributes:
        url (str | None): The URL for the authentication endpoint, if applicable.
        username (str): The username used for authentication.
        password (str): The password used for authentication.
        isDefault (bool): Denotes if this user should be used if no username is specified. Must be true for only one object within auth.
    """

    url: str | None = None
    username: str
    password: str
    isDefault: bool = False
