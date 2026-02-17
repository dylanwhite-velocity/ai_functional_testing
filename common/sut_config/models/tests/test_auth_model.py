"""Unit tests for AuthModel."""

from common.sut_config.models.auth_model import AuthModel


def test_auth_model_fields():
    """Test that fields are set correctly."""
    auth = AuthModel(url="http://example.com", username="user", password="pass", isDefault=True)
    assert auth.url == "http://example.com"
    assert auth.username == "user"
    assert auth.password == "pass"
    assert auth.isDefault is True


def test_auth_model_default_values():
    """Test that default values are set correctly."""
    auth = AuthModel(username="user", password="pass")
    assert auth.url is None
    assert auth.isDefault is False
