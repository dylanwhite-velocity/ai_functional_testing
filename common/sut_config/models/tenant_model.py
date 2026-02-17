"""A Pydantic model representing a single tenant within the system under test."""

from pydantic import BaseModel, model_validator

from common.sut_config.models.auth_model import AuthModel


class TenantModel(BaseModel):
    """A Pydantic model representing a tenant in the system under test.

    Attributes:
        is_default (bool): Denotes if this tenant should be used if no orgid is specified. Must be true for only one object within tenants.
        orgId (str | None): The organization ID for the tenant, if applicable.
        auth (list[AuthModel]): A list of authentication objects for this tenant.
    """

    isDefault: bool = False
    orgId: str | None = None
    auth: list[AuthModel]

    @model_validator(mode="before")
    @classmethod
    def validate_auth_default(cls, values):
        """Ensure exactly one auth entry has isDefault=True.

        Raises ValueError if not exactly one is set.
        """
        # Validate each object in auth_list is an AuthModel
        auth_model_list = [AuthModel.model_validate(a) for a in values.get("auth", [])]

        default_count = sum(1 for a in auth_model_list if a.isDefault)
        if default_count != 1:
            raise ValueError(f"Exactly one auth entry must have isDefault=True, {default_count} auth entries found with isDefault=True.")
        return values

    def get_default_auth(self) -> AuthModel:
        """Return the default auth for this system under test.

        Raises:
            ValueError: If no tenant is marked as default.
        """
        for auth in self.auth:
            if auth.isDefault:
                return auth
        raise ValueError("No default auth found.")

    def get_auth_with_username(self, username: str) -> AuthModel:
        """Return the auth for this tenant that matches the given username.

        Args:
            username (str): The username to match.

        Returns:
            AuthModel: The auth that matches the given username.

        Raises:
            ValueError: If no auth is found with the given username.
        """
        for auth in self.auth:
            if auth.username == username:
                return auth
        raise ValueError(f"No auth found with username: {username}")
