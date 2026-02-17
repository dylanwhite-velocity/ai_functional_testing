"""Unit tests for SUTConfigManager."""

from unittest.mock import MagicMock, patch

import pytest

from common.sut_config.models.sut_config_model import SUTConfigModel
from common.sut_config.sut_config_manager import SUTConfigManager


@pytest.fixture(autouse=True)
def clear_sutconfigmanager_cache():
    """Automatically clear SUTConfigManager cache before each test."""
    SUTConfigManager._config_cache.clear()


@pytest.fixture
def sut_config_manager():
    """Fixture."""
    return SUTConfigManager()


@patch("common.sut_config.sut_config_manager.aws_utils.get_secret")
def test_get_config_from_remote_success(mock_get_secret, sut_config_manager):
    """Test get_config_from_remote returns a SUTConfigModel on success."""
    mock_json = '{"name": "env", "distribution": "GeoEvent", "apiUrl": "http://api", "tenants": [{"isDefault": true, "orgId": "org1", "auth": [{"username": "user", "password": "pass", "isDefault": true}]}]}'  # noqa: E501
    mock_get_secret.return_value = mock_json
    config = sut_config_manager.get_config_from_remote("env")
    assert isinstance(config, SUTConfigModel)
    assert config.name == "env"


@patch("common.sut_config.sut_config_manager.aws_utils.list_secrets_with_prefix")
def test_list_available_configs_success(mock_list_secrets, sut_config_manager):
    """Test list_available_configs returns config names."""
    mock_list_secrets.return_value = ["RASP/SUTConfig/env1", "RASP/SUTConfig/env2"]
    configs = sut_config_manager.list_available_configs()
    assert configs == ["env1", "env2"]


@patch("common.sut_config.sut_config_manager.config_utils.save_config_file")
@patch.object(SUTConfigManager, "get_config_from_remote")
def test_set_active_context(mock_get_config, mock_save, sut_config_manager):
    """Test set_active_context saves the correct marker."""
    mock_config = MagicMock()
    mock_config.name = "env"
    mock_config.get_default_tenant.return_value = MagicMock(orgId="org1", get_default_auth=MagicMock(return_value=MagicMock(username="user")))
    mock_config.get_tenant_with_username.return_value = None
    mock_config.get_tenant_with_orgid.return_value = None
    mock_get_config.return_value = mock_config
    sut_config_manager.set_active_context("env")
    mock_save.assert_called_once()


@patch("common.sut_config.sut_config_manager.config_utils.get_config_file")
@patch.object(SUTConfigManager, "get_config_from_remote")
def test_get_config_and_marker(mock_get_config, mock_get_file, sut_config_manager):
    """Test get_config returns config from cache and marker."""
    mock_get_file.return_value = {"environmentName": "env", "username": "user"}
    mock_config = MagicMock()
    mock_get_config.return_value = mock_config
    # First call populates cache
    config = sut_config_manager.get_config()
    assert config == mock_config
    # Second call should use cache
    config2 = sut_config_manager.get_config()
    assert config2 == mock_config


@patch("common.sut_config.sut_config_manager.config_utils.get_config_file")
@patch.object(SUTConfigManager, "get_config_from_remote")
def test_get_tenant_and_auth(mock_get_config, mock_get_file):
    """Test get_tenant and get_auth return correct models."""
    sut_config_manager = SUTConfigManager()
    mock_get_file.return_value = {"environmentName": "env", "username": "user"}
    mock_config = MagicMock()
    tenant = MagicMock()
    auth = MagicMock()
    mock_config.get_tenant_with_username.return_value = tenant
    mock_config.get_default_tenant.return_value = tenant
    tenant.get_auth_with_username.return_value = auth
    tenant.get_default_auth.return_value = auth
    mock_get_config.return_value = mock_config
    assert sut_config_manager.get_tenant() == tenant
    assert sut_config_manager.get_auth() == auth


@patch("common.sut_config.sut_config_manager.config_utils.get_config_file", return_value=None)
def test_get_active_config_marker_none(mock_get_file, sut_config_manager):
    """Test __get_active_config_marker raises if marker is missing."""
    with pytest.raises(ValueError):
        sut_config_manager.get_config()
