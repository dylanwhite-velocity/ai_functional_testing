"""A Pydantic Model representing a system under test configuration for use in all RASP tools."""

from typing import Any, Literal

from pydantic import BaseModel, model_validator

from common.sut_config.models.tenant_model import TenantModel


class SUTConfigModel(BaseModel):
    """A Pydantic Model representing a system under test configuration for use in all RASP tools.

    Attributes:
        name (str): The commonly referred to name for the system under test / environment.
        distribution (Literal["VelocitySaaS", "VelocityEnterprise", "GeoEvent"]): The type of system under test.
        target (TargetModel): The target system configuration, including API URL, tenants, and metadata.
    """

    name: str
    distribution: Literal["VelocitySaaS", "VelocityEnterprise", "GeoEvent"]
    apiUrl: str
    licenseLevel: Literal["DEDICATED", "ADVANCED", "STANDARD"] | None = None
    tenants: list[TenantModel]
    additionalMetadata: dict[str, Any] | None = None

    @model_validator(mode="before")
    @classmethod
    def validate_tenant_default(cls, values):
        """Ensure exactly one tenant entry has isDefault=True.

        Raises ValueError if not exactly one is set.
        """
        tenant_models = [TenantModel.model_validate(a) for a in values.get("tenants", [])]
        default_count = sum(1 for t in tenant_models if t.isDefault)
        if default_count != 1:
            raise ValueError(f"Exactly one tenant entry must have isDefault=True, {default_count} tenant entries found with isDefault=True.")
        return values

    def get_default_tenant(self) -> TenantModel:
        """Return the default tenant for this system under test.

        Raises:
            ValueError: If no tenant is marked as default.
        """
        for tenant in self.tenants:
            if tenant.isDefault:
                return tenant
        raise ValueError("No tenant is marked as default.")

    def get_tenant_with_username(self, username: str) -> TenantModel:
        """Return the tenant for this system under test that matches the given username.

        Args:
            username (str): The username to match.

        Returns:
            TenantModel: The tenant that matches the given username.

        Raises:
            ValueError: If no tenant is found with the given username.
        """
        for tenant in self.tenants:
            for auth in tenant.auth:
                if auth.username == username:
                    return tenant
        raise ValueError(f"No tenant found with username: {username}")

    def get_tenant_with_orgid(self, org_id: str) -> TenantModel:
        """Return the tenant for this system under test that matches the given org id.

        Args:
            org_id (str): The org id to match.

        Returns:
            TenantModel: The tenant that matches the given org id.

        Raises:
            ValueError: If no tenant is found with the given org id.
        """
        for tenant in self.tenants:
            if tenant.orgId == org_id:
                return tenant
        raise ValueError(f"No tenant found with org id: {org_id}")
