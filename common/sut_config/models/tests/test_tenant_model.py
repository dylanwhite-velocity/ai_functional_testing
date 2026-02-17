"""Unit tests for TenantModel."""

import pytest

from common.sut_config.models.auth_model import AuthModel
from common.sut_config.models.tenant_model import TenantModel


def test_tenant_model_fields():
    """Test that fields are set correctly."""
    auth1 = AuthModel(username="user1", password="pass1", isDefault=True)
    tenant = TenantModel(isDefault=True, orgId="org1", auth=[auth1])
    assert tenant.isDefault is True
    assert tenant.orgId == "org1"
    assert tenant.auth[0].username == "user1"


def test_get_default_auth():
    """Test get_default_auth returns the correct AuthModel."""
    auth1 = AuthModel(username="user1", password="pass1", isDefault=True)
    auth2 = AuthModel(username="user2", password="pass2", isDefault=False)
    tenant = TenantModel(isDefault=True, orgId="org1", auth=[auth1, auth2])
    assert tenant.get_default_auth().username == "user1"


def test_get_auth_with_username_found():
    """Test get_auth_with_username returns the correct AuthModel when found."""
    auth1 = AuthModel(username="user1", password="pass1", isDefault=True)
    auth2 = AuthModel(username="user2", password="pass2", isDefault=False)
    tenant = TenantModel(isDefault=True, orgId="org1", auth=[auth1, auth2])
    assert tenant.get_auth_with_username("user2").password == "pass2"


def test_get_auth_with_username_not_found():
    """Test get_auth_with_username raises ValueError when username not found."""
    auth1 = AuthModel(username="user1", password="pass1", isDefault=True)
    tenant = TenantModel(isDefault=True, orgId="org1", auth=[auth1])
    with pytest.raises(ValueError):
        tenant.get_auth_with_username("notfound")


def test_validate_auth_default_raises():
    """Test model_validator raises if not exactly one default auth."""
    with pytest.raises(ValueError):
        TenantModel.model_validate(
            {
                "isDefault": True,
                "orgId": "org1",
                "auth": [
                    {"username": "user1", "password": "pass1", "isDefault": False},
                    {"username": "user2", "password": "pass2", "isDefault": False},
                ],
            }
        )
