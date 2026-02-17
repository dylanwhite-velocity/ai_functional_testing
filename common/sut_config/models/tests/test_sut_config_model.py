"""Unit tests for SUTConfigModel."""

import json

import pytest

from common.sut_config.models.auth_model import AuthModel
from common.sut_config.models.sut_config_model import SUTConfigModel
from common.sut_config.models.tenant_model import TenantModel


def make_tenant(username, orgid, is_default_tenant=False, is_default_auth=False):
    """Helper function to create a TenantModel."""
    auth = AuthModel(username=username, password="pass", isDefault=is_default_auth)
    return TenantModel(isDefault=is_default_tenant, orgId=orgid, auth=[auth])


def test_sut_config_model_fields():
    """Test that fields are set correctly."""
    tenant = make_tenant("user1", "org1", True, True)
    config = SUTConfigModel(
        name="testenv",
        distribution="GeoEvent",
        apiUrl="http://api",
        tenants=[tenant],
    )
    assert config.name == "testenv"
    assert config.apiUrl == "http://api"
    assert config.tenants[0].orgId == "org1"


def test_get_default_tenant():
    """Test get_default_tenant returns the correct tenant."""
    tenant1 = make_tenant("user1", "org1", True, True)
    tenant2 = make_tenant("user2", "org2", False, True)
    config = SUTConfigModel(
        name="testenv",
        distribution="GeoEvent",
        apiUrl="http://api",
        tenants=[tenant1, tenant2],
    )
    assert config.get_default_tenant().orgId == "org1"


def test_get_tenant_with_username_found():
    """Test get_tenant_with_username returns the correct tenant when found."""
    tenant1 = make_tenant("user1", "org1", True, True)
    tenant2 = make_tenant("user2", "org2", False, True)
    config = SUTConfigModel(
        name="testenv",
        distribution="GeoEvent",
        apiUrl="http://api",
        tenants=[tenant1, tenant2],
    )
    assert config.get_tenant_with_username("user2").orgId == "org2"


def test_get_tenant_with_username_not_found():
    """Test get_tenant_with_username raises ValueError when not found."""
    tenant1 = make_tenant("user1", "org1", True, True)
    config = SUTConfigModel(
        name="testenv",
        distribution="GeoEvent",
        apiUrl="http://api",
        tenants=[tenant1],
    )
    with pytest.raises(ValueError):
        config.get_tenant_with_username("notfound")


def test_get_tenant_with_orgid_found():
    """Test get_tenant_with_orgid returns the correct tenant when found."""
    tenant1 = make_tenant("user1", "org1", True, True)
    tenant2 = make_tenant("user2", "org2", False, True)
    config = SUTConfigModel(
        name="testenv",
        distribution="GeoEvent",
        apiUrl="http://api",
        tenants=[tenant1, tenant2],
    )
    assert config.get_tenant_with_orgid("org2").auth[0].username == "user2"


def test_get_tenant_with_orgid_not_found():
    """Test get_tenant_with_orgid raises ValueError when not found."""
    tenant1 = make_tenant("user1", "org1", True, True)
    config = SUTConfigModel(
        name="testenv",
        distribution="GeoEvent",
        apiUrl="http://api",
        tenants=[tenant1],
    )
    with pytest.raises(ValueError):
        config.get_tenant_with_orgid("notfound")


def test_validate_tenant_default_raises():
    """Test model_validator raises if not exactly one default tenant."""
    with pytest.raises(ValueError):
        SUTConfigModel.model_validate(
            {
                "name": "testenv",
                "distribution": "GeoEvent",
                "apiUrl": "http://api",
                "tenants": [
                    {"isDefault": False, "orgId": "org1", "auth": [{"username": "user1", "password": "pass", "isDefault": True}]},
                    {"isDefault": False, "orgId": "org2", "auth": [{"username": "user2", "password": "pass", "isDefault": True}]},
                ],
            }
        )


def test_tenantmodel_from_json():
    """Test TenantModel can be created from a JSON string using Pydantic."""
    json_str = '{"isDefault": true, "orgId": "org1", "auth": [{"username": "user1", "password": "pass1", "isDefault": true}]}'
    data = json.loads(json_str)
    tenant = TenantModel.model_validate(data)
    assert tenant.isDefault is True
    assert tenant.orgId == "org1"
    assert tenant.auth[0].username == "user1"


def test_authmodel_from_json():
    """Test AuthModel can be created from a JSON string using Pydantic."""
    json_str = '{"username": "user1", "password": "pass1", "isDefault": true}'
    data = json.loads(json_str)
    auth = AuthModel.model_validate(data)
    assert auth.username == "user1"
    assert auth.password == "pass1"
    assert auth.isDefault is True
