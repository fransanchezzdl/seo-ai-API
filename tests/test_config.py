from unittest.mock import Mock

import pytest

from app import config


@pytest.fixture(autouse=True)
def clean_config(monkeypatch):
    config.get_client.cache_clear()
    for key in ["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "OPENAI_API_KEY"]:
        monkeypatch.delenv(key, raising=False)
    yield
    config.get_client.cache_clear()


def test_azure_client(monkeypatch):
    factory = Mock()
    monkeypatch.setattr(config, "AzureOpenAI", factory)
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "fake")
    config.get_client()
    config.get_client()
    factory.assert_called_once()
    assert factory.call_args.kwargs["api_key"] == "fake"
    assert factory.call_args.kwargs["timeout"] == 90


def test_incomplete_azure_does_not_fallback(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "fake")
    monkeypatch.setenv("OPENAI_API_KEY", "fake")
    with pytest.raises(config.ConfigurationError):
        config.get_client()


def test_no_credentials():
    with pytest.raises(config.ConfigurationError):
        config.get_client()


def test_direct_client(monkeypatch):
    factory = Mock()
    monkeypatch.setattr(config, "OpenAI", factory)
    monkeypatch.setenv("OPENAI_API_KEY", "fake")
    config.get_client()
    assert factory.call_args.kwargs["api_key"] == "fake"
