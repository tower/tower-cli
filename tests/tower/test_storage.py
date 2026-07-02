from datetime import datetime, timedelta, timezone

import pytest

from tower._context import TowerContext
from tower import _storage
from tower.tower_api_client.models import CatalogCredentials


def clear_tower_env(monkeypatch):
    for name in (
        "TOWER_URL",
        "TOWER_ENVIRONMENT",
        "TOWER_API_KEY",
        "TOWER_JWT",
        "TOWER__RUNTIME__RUN_ID",
        "TOWER__RUNTIME__ENVIRONMENT_NAME",
    ):
        monkeypatch.delenv(name, raising=False)


def test_context_prefers_runtime_environment(monkeypatch, tmp_path):
    clear_tower_env(monkeypatch)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("TOWER_ENVIRONMENT", "local-env")
    monkeypatch.setenv("TOWER__RUNTIME__ENVIRONMENT_NAME", "run-env")

    ctx = TowerContext.build()

    assert ctx.environment == "run-env"


def test_context_treats_blank_auth_env_as_missing(monkeypatch, tmp_path):
    clear_tower_env(monkeypatch)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("TOWER_URL", "")
    monkeypatch.setenv("TOWER_API_KEY", "")
    monkeypatch.setenv("TOWER_JWT", "")

    ctx = TowerContext.build()

    assert ctx.tower_url == "https://api.tower.dev"
    assert ctx.api_key is None
    assert ctx.jwt is None


def test_vending_requires_explicit_credentials(monkeypatch):
    _storage._clear_credential_cache()
    ctx = TowerContext(tower_url="https://api.example.com", environment="production")
    monkeypatch.setattr(_storage.TowerContext, "build", staticmethod(lambda: ctx))

    with pytest.raises(RuntimeError, match="No Tower authentication found"):
        _storage.get_tower_catalog_credentials("default")


def test_get_tower_catalog_credentials_caches_vended_credentials(monkeypatch):
    _storage._clear_credential_cache()
    ctx = TowerContext(
        tower_url="https://api.example.com",
        environment="production",
        api_key="api-key",
    )
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    credentials = CatalogCredentials(
        catalog_uri="https://catalog.example.com",
        expires_at=expires_at,
        mode="read",
        oauth_token="oauth-token",
        warehouse="warehouse-id",
    )
    calls = []

    def try_vend(ctx, name, environment, mode):
        calls.append((name, environment, mode))
        return credentials

    monkeypatch.setattr(_storage.TowerContext, "build", staticmethod(lambda: ctx))
    monkeypatch.setattr(_storage, "_try_vend", try_vend)

    first = _storage.get_tower_catalog_credentials("default")
    second = _storage.get_tower_catalog_credentials("default")

    assert first is credentials
    assert second is credentials
    assert calls == [("default", "production", "read")]


def test_get_tower_catalog_credentials_prunes_expired_cache_entries(monkeypatch):
    _storage._clear_credential_cache()
    ctx = TowerContext(
        tower_url="https://api.example.com",
        environment="production",
        api_key="api-key",
    )
    expired_credentials = CatalogCredentials(
        catalog_uri="https://old-catalog.example.com",
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        mode="read",
        oauth_token="old-oauth-token",
        warehouse="old-warehouse-id",
    )
    fresh_credentials = CatalogCredentials(
        catalog_uri="https://catalog.example.com",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        mode="read",
        oauth_token="oauth-token",
        warehouse="warehouse-id",
    )
    expired_key = (ctx.tower_url, "api-key", "stale", "production", "read")
    _storage._credential_cache[expired_key] = expired_credentials

    def try_vend(ctx, name, environment, mode):
        return fresh_credentials

    monkeypatch.setattr(_storage.TowerContext, "build", staticmethod(lambda: ctx))
    monkeypatch.setattr(_storage, "_try_vend", try_vend)

    result = _storage.get_tower_catalog_credentials("default")

    assert result is fresh_credentials
    assert expired_key not in _storage._credential_cache


def test_default_catalog_vend_retries_after_provisioning(monkeypatch):
    _storage._clear_credential_cache()
    ctx = TowerContext(
        tower_url="https://api.example.com",
        environment="default",
        api_key="api-key",
    )
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    credentials = CatalogCredentials(
        catalog_uri="https://catalog.example.com",
        expires_at=expires_at,
        mode="read",
        oauth_token="oauth-token",
        warehouse="warehouse-id",
    )
    responses = [None, None, credentials]
    provision_calls = []

    def try_vend(ctx, name, environment, mode):
        return responses.pop(0)

    def provision_default(ctx):
        provision_calls.append(ctx)

    monkeypatch.setattr(_storage.TowerContext, "build", staticmethod(lambda: ctx))
    monkeypatch.setattr(_storage, "_try_vend", try_vend)
    monkeypatch.setattr(_storage, "_provision_default_catalog", provision_default)
    monkeypatch.setattr(_storage.time, "sleep", lambda delay: None)

    result = _storage.get_tower_catalog_credentials("default")

    assert result is credentials
    assert len(provision_calls) == 2
