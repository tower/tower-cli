from datetime import datetime, timedelta, timezone
from http import HTTPStatus

import httpx
import pytest

from tower import _storage
from tower._context import TowerContext
from tower.exceptions import (
    StorageConnectionError,
    StorageInvalidCredentialError,
    StorageMissingAuthenticationError,
)
from tower.tower_api_client.models import (
    Catalog,
    CatalogCredentials,
    DescribeCatalogResponse,
    ErrorModel,
    VendCatalogCredentialsResponse,
)


@pytest.fixture(autouse=True)
def isolate_tower_environment(monkeypatch, tmp_path):
    for name in (
        "TOWER_URL",
        "TOWER_ENVIRONMENT",
        "TOWER_API_KEY",
        "TOWER_JWT",
        "TOWER__RUNTIME__RUN_ID",
        "TOWER__RUNTIME__ENVIRONMENT_NAME",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))


def test_context_prefers_runtime_environment(monkeypatch):
    monkeypatch.setenv("TOWER_ENVIRONMENT", "local-env")
    monkeypatch.setenv("TOWER__RUNTIME__ENVIRONMENT_NAME", "run-env")

    ctx = TowerContext.build()

    assert ctx.environment == "run-env"


def test_context_treats_blank_auth_env_as_missing(monkeypatch):
    monkeypatch.setenv("TOWER_URL", "")
    monkeypatch.setenv("TOWER_API_KEY", "")
    monkeypatch.setenv("TOWER_JWT", "")

    ctx = TowerContext.build()

    assert ctx.tower_url == "https://api.tower.dev"
    assert ctx.api_key is None
    assert ctx.jwt is None


def test_storage_resolver_configuration_and_tls_defaults(monkeypatch):
    monkeypatch.setenv("TOWER_URL", "https://tower.example.com/")
    monkeypatch.setenv("TOWER_API_KEY", "ambient-key")
    resolver = _storage._StorageResolver(environment="production")
    client = resolver._new_client()

    assert resolver._target_environment == "production"
    assert resolver._base_url == "https://tower.example.com/v1"
    assert client._base_url == "https://tower.example.com/v1"
    assert client._timeout == httpx.Timeout(_storage.DEFAULT_STORAGE_TIMEOUT_SECONDS)
    assert client._verify_ssl is True

    http_client = client.get_httpx_client()
    try:
        assert http_client.headers["X-API-Key"] == "ambient-key"
        assert "Authorization" not in http_client.headers
    finally:
        http_client.close()


@pytest.mark.parametrize(
    ("ambient_auth", "expected_header", "expected_value"),
    [
        (
            {"TOWER_API_KEY": "ambient-key", "TOWER_JWT": "ambient-jwt"},
            "Authorization",
            "Bearer ambient-jwt",
        ),
        ({"TOWER_API_KEY": "ambient-key"}, "X-API-Key", "ambient-key"),
    ],
    ids=("jwt-over-api-key", "api-key-fallback"),
)
def test_storage_resolver_static_auth_precedence(
    monkeypatch,
    ambient_auth,
    expected_header,
    expected_value,
):
    for name, value in ambient_auth.items():
        monkeypatch.setenv(name, value)

    client = _storage._StorageResolver()._new_client()
    http_client = client.get_httpx_client()
    try:
        assert http_client.headers[expected_header] == expected_value
        other_header = (
            "Authorization" if expected_header == "X-API-Key" else "X-API-Key"
        )
        assert other_header not in http_client.headers
    finally:
        http_client.close()


def test_auth_hash_includes_how_the_credential_is_presented():
    assert _storage._auth_hash("same-token", "Authorization", "Bearer") != (
        _storage._auth_hash("same-token", "X-API-Key", "")
    )


def test_missing_auth_fails_before_cache_or_vend(monkeypatch):
    _storage._clear_credential_cache()

    monkeypatch.setattr(
        _storage,
        "_prune_credential_cache",
        lambda now: pytest.fail("cache access must not run without authentication"),
    )
    monkeypatch.setattr(
        _storage.vend_catalog_credentials_api,
        "sync",
        lambda **kwargs: pytest.fail("vend must not run without authentication"),
    )

    with pytest.raises(StorageMissingAuthenticationError):
        _storage.get_tower_catalog_credentials("analytics")


def test_storage_resolver_rejects_redacted_jwt_without_falling_back(monkeypatch):
    monkeypatch.setenv("TOWER_JWT", " <redacted> ")
    monkeypatch.setenv("TOWER_API_KEY", "otherwise-valid-api-key")

    with pytest.raises(StorageInvalidCredentialError):
        _storage._StorageResolver()


@pytest.mark.parametrize("status", [HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN])
def test_static_auth_rejection_is_returned(monkeypatch, status):
    monkeypatch.setenv("TOWER_JWT", "ambient-jwt")
    rejected = ErrorModel(status=int(status), detail="rejected")
    vend_calls = []

    def vend(**kwargs):
        vend_calls.append(kwargs)
        return rejected

    monkeypatch.setattr(_storage.vend_catalog_credentials_api, "sync", vend)

    result = _storage._StorageResolver()._request_catalog_credentials(
        "analytics", "read"
    )

    assert result is rejected
    assert len(vend_calls) == 1


def test_storage_resolver_vends_with_ambient_api_key(monkeypatch):
    monkeypatch.setenv("TOWER_URL", "https://api.example.com")
    monkeypatch.setenv("TOWER_API_KEY", "service-account-key")
    captured = {}
    clients = []
    response = ErrorModel(status=418, detail="captured")

    def vend(*, name, client, environment, body):
        clients.append(client)
        http_client = client.get_httpx_client()
        captured.update(
            name=name,
            environment=environment,
            api_key=http_client.headers.get("X-API-Key"),
            authorization=http_client.headers.get("Authorization"),
            mode=body.mode,
        )
        return response

    monkeypatch.setattr(_storage.vend_catalog_credentials_api, "sync", vend)

    result = _storage._StorageResolver(
        environment="production"
    )._request_catalog_credentials("analytics", "read")

    assert result is response
    assert captured == {
        "name": "analytics",
        "environment": "production",
        "api_key": "service-account-key",
        "authorization": None,
        "mode": _storage.VendCatalogCredentialsBodyMode.READ,
    }
    assert clients[0]._client is not None
    assert clients[0]._client.is_closed


def test_describe_and_vend_prefer_jwt_when_both_auth_vars_are_set(monkeypatch):
    _storage._clear_credential_cache()
    monkeypatch.setenv("TOWER_URL", "https://api.example.com")
    monkeypatch.setenv("TOWER_ENVIRONMENT", "production")
    monkeypatch.setenv("TOWER_API_KEY", "ambient-api-key")
    monkeypatch.setenv("TOWER_JWT", "ambient-jwt")
    captured_auth = []

    def capture_auth(operation, client):
        http_client = client.get_httpx_client()
        captured_auth.append(
            (
                operation,
                http_client.headers.get("Authorization"),
                http_client.headers.get("X-API-Key"),
            )
        )

    def describe(*, name, client, environment):
        capture_auth("describe", client)
        return DescribeCatalogResponse(
            catalog=Catalog(
                created_at=datetime.now(timezone.utc),
                environment=environment,
                name=name,
                properties=[],
                type_=_storage.TOWER_CATALOG_TYPE,
            )
        )

    vended = ErrorModel(status=418, detail="captured")

    def vend(*, client, **kwargs):
        capture_auth("vend", client)
        return vended

    monkeypatch.setattr(_storage.describe_catalog_api, "sync", describe)
    monkeypatch.setattr(_storage.vend_catalog_credentials_api, "sync", vend)

    ctx = TowerContext.build()
    assert (
        _storage._describe_tower_catalog_type(ctx, "analytics", "production")
        == _storage.TOWER_CATALOG_TYPE
    )
    assert (
        _storage._StorageResolver()._request_catalog_credentials("analytics", "read")
        is vended
    )
    assert captured_auth == [
        ("describe", "Bearer ambient-jwt", None),
        ("vend", "Bearer ambient-jwt", None),
    ]


def test_storage_resolver_allows_explicit_http_tower_url(monkeypatch):
    monkeypatch.setenv("TOWER_URL", "http://localhost:9000")
    monkeypatch.setenv("TOWER_API_KEY", "key")
    client = _storage._StorageResolver()._new_client()

    assert client._base_url == "http://localhost:9000/v1"
    assert client._verify_ssl is True


def test_get_tower_catalog_credentials_allows_http_and_reaches_vend(monkeypatch):
    _storage._clear_credential_cache()
    monkeypatch.setenv("TOWER_URL", "http://localhost:9000")
    monkeypatch.setenv("TOWER_ENVIRONMENT", "production")
    monkeypatch.setenv("TOWER_API_KEY", "api-key")
    credentials = CatalogCredentials(
        catalog_uri="http://catalog.example.com",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        mode="read",
        oauth_token="oauth-token",
        warehouse="warehouse-id",
    )
    vend_calls = []

    def vend(*, name, client, environment, body):
        vend_calls.append(
            (name, client._base_url, client._verify_ssl, environment, body.mode)
        )
        return VendCatalogCredentialsResponse(
            credentials=credentials,
            environment=environment,
        )

    monkeypatch.setattr(_storage.vend_catalog_credentials_api, "sync", vend)

    result = _storage.get_tower_catalog_credentials("analytics")

    assert result is credentials
    assert vend_calls == [
        (
            "analytics",
            "http://localhost:9000/v1",
            True,
            "production",
            _storage.VendCatalogCredentialsBodyMode.READ,
        )
    ]


def test_storage_resolver_normalizes_and_validates_tower_api_url(monkeypatch):
    monkeypatch.setenv(
        "TOWER_URL",
        "https://TOWER.example.com:443/old/path?debug=true#fragment",
    )
    monkeypatch.setenv("TOWER_API_KEY", "key")
    resolver = _storage._StorageResolver()
    assert resolver._base_url == "https://tower.example.com/v1"

    with pytest.raises(ValueError, match="Invalid Tower URL"):
        _storage._api_base_url("not-a-url")


def test_get_tower_catalog_credentials_rejects_invalid_mode_before_cache_or_vend(
    monkeypatch,
):
    monkeypatch.setenv("TOWER_API_KEY", "api-key")
    monkeypatch.setattr(
        _storage,
        "_prune_credential_cache",
        lambda now: pytest.fail("cache access must not run for an invalid mode"),
    )
    monkeypatch.setattr(
        _storage.vend_catalog_credentials_api,
        "sync",
        lambda **kwargs: pytest.fail("vend must not run for an invalid mode"),
    )

    with pytest.raises(ValueError, match="mode must be 'read' or 'read-write'"):
        _storage.get_tower_catalog_credentials("analytics", mode="write")


def test_storage_resolver_rejects_invalid_environment():
    with pytest.raises(TypeError, match="environment must be a string or None"):
        _storage._StorageResolver(environment=123)
    with pytest.raises(ValueError, match="environment must not be blank"):
        _storage._StorageResolver(environment=" ")


def test_storage_resolver_maps_connection_errors_and_closes_client(monkeypatch):
    monkeypatch.setenv("TOWER_API_KEY", "key")
    cause = httpx.ConnectError("connection refused")
    clients = []

    def vend(*, client, **kwargs):
        clients.append(client)
        raise cause

    monkeypatch.setattr(_storage.vend_catalog_credentials_api, "sync", vend)

    with pytest.raises(StorageConnectionError) as error:
        _storage._StorageResolver()._request_catalog_credentials("analytics", "read")

    assert error.value.__cause__ is cause
    assert clients[0]._client is not None
    assert clients[0]._client.is_closed


def test_storage_resolver_uses_runtime_environment_only_as_target_config(monkeypatch):
    monkeypatch.setenv("TOWER_API_KEY", "key")
    monkeypatch.setenv("TOWER_ENVIRONMENT", "ambient-env")
    monkeypatch.setenv("TOWER__RUNTIME__ENVIRONMENT_NAME", "run-env")

    assert _storage._StorageResolver()._target_environment == "run-env"
    assert (
        _storage._StorageResolver(environment="explicit-env")._target_environment
        == "explicit-env"
    )


def test_get_tower_catalog_credentials_caches_vended_credentials(monkeypatch):
    _storage._clear_credential_cache()
    monkeypatch.setenv("TOWER_URL", "https://api.example.com")
    monkeypatch.setenv("TOWER_ENVIRONMENT", "production")
    monkeypatch.setenv("TOWER_API_KEY", "api-key")
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    credentials = CatalogCredentials(
        catalog_uri="https://catalog.example.com",
        expires_at=expires_at,
        mode="read",
        oauth_token="oauth-token",
        warehouse="warehouse-id",
    )
    calls = []

    def vend(client, name, mode):
        calls.append((name, client._target_environment, mode))
        return VendCatalogCredentialsResponse(
            credentials=credentials,
            environment=client._target_environment,
        )

    monkeypatch.setattr(_storage._StorageResolver, "_request_catalog_credentials", vend)

    first = _storage.get_tower_catalog_credentials("default")
    second = _storage.get_tower_catalog_credentials("default")

    assert first is credentials
    assert second is credentials
    assert calls == [("default", "production", "read")]


def test_get_tower_catalog_credentials_prunes_expired_cache_entries(monkeypatch):
    _storage._clear_credential_cache()
    monkeypatch.setenv("TOWER_URL", "https://api.example.com")
    monkeypatch.setenv("TOWER_ENVIRONMENT", "production")
    monkeypatch.setenv("TOWER_API_KEY", "api-key")
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
    storage_resolver = _storage._StorageResolver()
    expired_key = _storage._cache_key(storage_resolver, "stale", "read")
    _storage._credential_cache[expired_key] = _storage._CachedCredentials(
        expired_credentials
    )

    def vend(client, name, mode):
        return VendCatalogCredentialsResponse(
            credentials=fresh_credentials,
            environment=client._target_environment,
        )

    monkeypatch.setattr(_storage._StorageResolver, "_request_catalog_credentials", vend)

    result = _storage.get_tower_catalog_credentials("default")

    assert result is fresh_credentials
    assert expired_key not in _storage._credential_cache


def test_default_catalog_retries_reuse_client_auth_snapshot(monkeypatch):
    _storage._clear_credential_cache()
    monkeypatch.setenv("TOWER_API_KEY", "operation-token")
    credentials = CatalogCredentials(
        catalog_uri="https://catalog.example.com",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        mode="read",
        oauth_token="oauth-token",
        warehouse="warehouse-id",
    )
    responses = [
        ErrorModel(status=404, detail="not found"),
        ErrorModel(status=404, detail="still provisioning"),
        VendCatalogCredentialsResponse(
            credentials=credentials,
            environment="default",
        ),
    ]
    vend_tokens = []
    legacy_tokens = []
    clients = []

    def vend(*, client, **kwargs):
        clients.append(client)
        vend_tokens.append(client.token)
        monkeypatch.setenv("TOWER_API_KEY", "changed-after-client-construction")
        return responses.pop(0)

    def legacy_default(*, client):
        clients.append(client)
        legacy_tokens.append(client.token)
        return ErrorModel(status=404, detail="not provisioned")

    monkeypatch.setattr(_storage.vend_catalog_credentials_api, "sync", vend)
    monkeypatch.setattr(
        _storage.describe_default_catalog_api,
        "sync",
        legacy_default,
    )
    monkeypatch.setattr(_storage.time, "sleep", lambda delay: None)

    result = _storage.get_tower_catalog_credentials("default")

    assert result is credentials
    assert vend_tokens == ["operation-token"] * 3
    assert legacy_tokens == ["operation-token"] * 2
    assert len({id(client) for client in clients}) == 5
    assert all(client._client is not None for client in clients)
    assert all(client._client.is_closed for client in clients)


def test_describe_tower_catalog_type_uses_timeout_and_recovers_after_cooldown(
    monkeypatch,
):
    _storage._clear_credential_cache()
    ctx = TowerContext(
        tower_url="https://api.example.com",
        environment="production",
        api_key="api-key",
    )
    now = {"value": 100.0}
    calls = []
    transports = []

    def describe_catalog_api_sync(name, client, environment):
        transports.append(client)
        calls.append((name, environment, client._timeout))
        if len(calls) == 1:
            raise TimeoutError("describe timed out")

        return DescribeCatalogResponse(
            catalog=Catalog(
                created_at=datetime.now(timezone.utc),
                environment=environment,
                name=name,
                properties=[],
                type_="s3-tables",
            )
        )

    monkeypatch.setattr(_storage.time, "monotonic", lambda: now["value"])
    monkeypatch.setattr(
        _storage.describe_catalog_api, "sync", describe_catalog_api_sync
    )

    assert _storage._describe_tower_catalog_type(ctx, "s3-tables", "production") is None
    assert _storage._describe_tower_catalog_type(ctx, "s3-tables", "production") is None
    assert calls == [
        (
            "s3-tables",
            "production",
            httpx.Timeout(_storage.CATALOG_TYPE_DESCRIBE_TIMEOUT_SECONDS),
        )
    ]

    now["value"] += _storage.CATALOG_TYPE_FAILURE_CACHE_TTL_SECONDS + 0.1

    assert (
        _storage._describe_tower_catalog_type(ctx, "s3-tables", "production")
        == "s3-tables"
    )
    assert (
        _storage._describe_tower_catalog_type(ctx, "s3-tables", "production")
        == "s3-tables"
    )
    assert calls == [
        (
            "s3-tables",
            "production",
            httpx.Timeout(_storage.CATALOG_TYPE_DESCRIBE_TIMEOUT_SECONDS),
        ),
        (
            "s3-tables",
            "production",
            httpx.Timeout(_storage.CATALOG_TYPE_DESCRIBE_TIMEOUT_SECONDS),
        ),
    ]
    assert all(transport._client is not None for transport in transports)
    assert all(transport._client.is_closed for transport in transports)
