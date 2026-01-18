"""
Tower Mock API Server

This is a MOCK API server that provides fake endpoints for testing Tower CLI
integration tests. It simulates the real Tower API without requiring actual
backend infrastructure.

IMPORTANT: When the real Tower API schema changes (after regenerating the client
from OpenAPI specs), this mock API must be updated to match. See README.md for
debugging steps when integration tests fail with schema errors.
"""

from fastapi import FastAPI, HTTPException, Response, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import json
import datetime
import uuid
import asyncio
import sys

app = FastAPI(
    title="Tower Mock API",
    description="A mock API server for Tower CLI testing.",
    version="1.0.0",
)

# Enable debug logging if --debug is passed
DEBUG_MODE = "--debug" in sys.argv


@app.middleware("http")
async def log_requests(request: Request, call_next):
    if DEBUG_MODE:
        print(f"DEBUG: {request.method} {request.url}")
    response = await call_next(request)
    if DEBUG_MODE:
        print(f"DEBUG: Response status: {response.status_code}")
    return response


# In-memory data stores for mock responses
mock_apps_db = {}
mock_secrets_db = {}
mock_teams_db = {}
mock_runs_db = {}
mock_schedules_db = {}
mock_deployed_apps = set()  # Track which apps have been deployed

# Pre-populate with test-app for CLI validation/spinner tests
mock_apps_db["predeployed-test-app"] = {
    "name": "predeployed-test-app",
    "owner": "mock_owner",
    "short_description": "Pre-existing test app for CLI tests",
    "version": None,
    "schedule": None,
    "created_at": datetime.datetime.now().isoformat(),
    "next_run_at": None,
    "health_status": "healthy",
    "run_results": {
        "cancelled": 0,
        "crashed": 0,
        "errored": 0,
        "exited": 0,
        "pending": 0,
        "running": 0,
    },
    "subdomain": None,
    "is_externally_accessible": False,
}
# Pre-deploy the test-app so it can be used for validation tests
mock_deployed_apps.add("predeployed-test-app")


def generate_id():
    return str(uuid.uuid4())


def now_iso():
    return datetime.datetime.now().isoformat()


def create_schedule_object(
    schedule_id, app_name, cron, environment="default", parameters=None
):
    return {
        "id": schedule_id,
        "app_name": app_name,
        "cron": cron,
        "environment": environment,
        "status": "active",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "parameters": parameters or [],
    }


@app.get("/")
async def read_root():
    return {"message": "Tower Mock API is running!"}


# Placeholder for /v1/apps endpoints
@app.get("/v1/apps")
async def list_apps():
    # Format apps as AppSummary objects
    app_summaries = []
    for app_data in mock_apps_db.values():
        app_summaries.append({"app": app_data, "runs": []})  # Empty runs for list view

    return {
        "apps": app_summaries,
        "pages": {
            "page": 1,
            "total": len(mock_apps_db),
            "num_pages": 1,
            "page_size": 20,
        },
    }


@app.post("/v1/apps", status_code=201)
async def create_app(app_data: Dict[str, Any]):
    app_name = app_data.get("name")
    if not app_name:
        raise HTTPException(status_code=400, detail="App name is required")

    # For testing purposes, always succeed even if app exists
    # Just return the existing app or create a new one
    if app_name in mock_apps_db:
        return {"app": mock_apps_db[app_name]}

    new_app = {
        "created_at": datetime.datetime.now().isoformat(),
        "health_status": "healthy",
        "is_externally_accessible": True,
        "name": app_name,
        "next_run_at": None,
        "owner": "mock_owner",
        "run_results": {
            "cancelled": 0,
            "crashed": 0,
            "errored": 0,
            "exited": 0,
            "pending": 0,
            "running": 0,
        },
        "schedule": None,
        "short_description": app_data.get("short_description", ""),
        "status": "active",
        "subdomain": "",
        "version": None,
    }
    mock_apps_db[app_name] = new_app
    return {"app": new_app}


@app.get("/v1/apps/{name}")
async def describe_app(name: str, response: Response):
    app_info = mock_apps_db.get(name)
    if not app_info:
        response.status_code = 404
        return {
            "$schema": "https://api.tower.dev/v1/schemas/ErrorModel.json",
            "title": "Not Found",
            "status": 404,
            "detail": f"App '{name}' not found",
        }
    return {"app": app_info, "runs": []}  # Simplistic, no runs yet


@app.delete("/v1/apps/{name}")
async def delete_app(name: str):
    if name not in mock_apps_db:
        raise HTTPException(status_code=404, detail=f"App '{name}' not found")
    deleted_app = mock_apps_db.pop(name)
    return {"app": deleted_app}


@app.post("/v1/apps/{name}/deploy")
async def deploy_app(name: str, response: Response):
    if name not in mock_apps_db:
        raise HTTPException(status_code=404, detail=f"App '{name}' not found")
    # Simulate a successful deployment
    version_num = "1.0.0"  # Simplified versioning
    deployed_version = {
        "version": version_num,
        "parameters": [],
        "created_at": datetime.datetime.now().isoformat(),
        "towerfile": "mock_towerfile_content",
    }
    # Update app's version and mark as deployed
    mock_apps_db[name]["version"] = version_num
    mock_deployed_apps.add(name)
    return {"version": deployed_version}


@app.post("/v1/apps/{name}/runs")
async def run_app(name: str, run_params: Dict[str, Any]):
    if name not in mock_apps_db:
        raise HTTPException(status_code=404, detail=f"App '{name}' not found")

    # Check if app has been deployed
    if name not in mock_deployed_apps:
        raise HTTPException(
            status_code=400,
            detail={
                "detail": f"App '{name}' has not been deployed yet. Please deploy the app first.",
                "status": 400,
                "title": "App Not Deployed",
            },
        )

    parameters = run_params.get("parameters", {})
    if "nonexistent_param" in parameters:
        raise HTTPException(
            status_code=422,
            detail={
                "detail": "Validation error",
                "status": 422,
                "title": "Unprocessable Entity",
                "errors": [{"message": "Unknown parameter"}],
            },
        )

    run_id = generate_id()
    new_run = {
        "$link": f"/runs/{run_id}",
        "run_id": run_id,
        "number": len(mock_runs_db) + 1,
        "app_name": name,
        "status": "running",
        "status_group": "",
        "parameters": [
            {"name": k, "value": v} for k, v in run_params.get("parameters", {}).items()
        ],
        "environment": run_params.get("environment", "default"),
        "exit_code": None,
        "created_at": datetime.datetime.now().isoformat(),
        "scheduled_at": datetime.datetime.now().isoformat(),
        "cancelled_at": None,
        "started_at": datetime.datetime.now().isoformat(),
        "ended_at": None,
        "app_version": mock_apps_db[name].get("version", "1.0.0"),
        "subdomain": None,
        "is_scheduled": True,
        "initiator": {
            "type": "tower_cli",
        },
    }
    mock_runs_db[run_id] = new_run
    return {"run": new_run}


@app.get("/v1/apps/{name}/runs/{seq}")
async def describe_run(name: str, seq: int):
    """Mock endpoint for describing a specific run."""
    if name not in mock_apps_db:
        raise HTTPException(status_code=404, detail=f"App '{name}' not found")

    # Find the run by sequence number (this is simplified)
    for run_id, run_data in mock_runs_db.items():
        if run_data["app_name"] == name and run_data["number"] == seq:
            # Simulate run progression: running -> exited after a few seconds
            import datetime

            created_time = datetime.datetime.fromisoformat(run_data["created_at"])
            now_time = datetime.datetime.now()
            elapsed = (now_time - created_time).total_seconds()

            # For logs-after-completion test apps, complete quickly to test log draining
            # Use 1 second so CLI has time to start streaming before completion
            completion_threshold = (
                1.0
                if "logs-after-completion" in name or "logs-warning" in name
                else 5.0
            )

            if elapsed > completion_threshold:
                run_data["status"] = "exited"
                run_data["status_group"] = "successful"
                run_data["exit_code"] = 0
                run_data["ended_at"] = now_time.isoformat()

            return {
                "run": run_data,
                "$links": {
                    "next": None,
                    "prev": None,
                    "self": run_data.get("$link"),
                },
            }

    raise HTTPException(
        status_code=404, detail=f"Run sequence {seq} not found for app '{name}'"
    )


# Placeholder for /secrets endpoints
@app.get("/v1/secrets")
async def list_secrets():
    return {
        "secrets": list(mock_secrets_db.values()),
        "pages": {
            "page": 1,
            "total": len(mock_secrets_db),
            "num_pages": 1,
            "page_size": 20,
        },
    }


@app.post("/v1/secrets")
async def create_secret(secret_data: Dict[str, Any]):
    secret_name = secret_data.get("name")
    environment = secret_data.get("environment", "default")
    key = f"{environment}/{secret_name}"
    if not secret_name:
        raise HTTPException(status_code=400, detail="Secret name is required")
    if key in mock_secrets_db:
        raise HTTPException(
            status_code=409,
            detail=f"Secret '{secret_name}' in environment '{environment}' already exists",
        )

    new_secret = {
        "name": secret_name,
        "environment": environment,
        "preview": secret_data.get("preview", "******"),
        "created_at": datetime.datetime.now().isoformat(),
    }
    mock_secrets_db[key] = new_secret
    return {"secret": new_secret}


@app.delete("/v1/secrets/{name}")
async def delete_secret(name: str, environment: str = "default"):
    key = f"{environment}/{name}"
    if key not in mock_secrets_db:
        raise HTTPException(
            status_code=404,
            detail=f"Secret '{name}' in environment '{environment}' not found",
        )
    deleted_secret = mock_secrets_db.pop(key)
    return {"secret": deleted_secret}


# Placeholder for /teams endpoints
@app.get("/v1/teams")
async def list_teams():
    return {"teams": list(mock_teams_db.values())}


@app.post("/v1/teams")
async def create_team(team_data: Dict[str, Any]):
    team_name = team_data.get("name")
    if not team_name:
        raise HTTPException(status_code=400, detail="Team name is required")
    if team_name in mock_teams_db:
        raise HTTPException(
            status_code=409, detail=f"Team '{team_name}' already exists"
        )

    new_team = {"name": team_name, "type": "team", "token": {"jwt": "mock_jwt_token"}}
    mock_teams_db[team_name] = new_team
    return {"team": new_team}


@app.put("/v1/teams/{name}")
async def switch_team(name: str):
    if name not in mock_teams_db:
        raise HTTPException(status_code=404, detail=f"Team '{name}' not found")
    # In a real scenario, this would involve updating the session/context
    # For mock, we just return the team
    return {"team": mock_teams_db[name]}


# Additional endpoints for MCP server support
@app.get("/v1/secrets/key")
async def describe_secrets_key():
    """Mock endpoint for getting secrets encryption key."""
    # Return a mock RSA public key
    mock_public_key = """-----BEGIN RSA PUBLIC KEY-----
MIIBCgKCAQEA2Z9QjRbVnqcXl6BjJpHhQY6LKhGkQY4nQSLp5QGx8xQzS1l5mKoT
2aJzQbJzXzJdQtJzMzJmYzY3YzIzMzJmYzMzNzJlYzNkYzNmYzQ1YzQ2YzQ3YzQ4
2Z9QjRbVnqcXl6BjJpHhQY6LKhGkQY4nQSLp5QGx8xQzS1l5mKoT2aJzQbJzXzJd
QzJmYzMzNzJlYzNkYzNmYzQ1YzQ2YzQ3YzQ4YzQ5YzUwYzUxYzUyYzUzYzU0YzU1
YzU2YzU3YzU4YzU5YzYwYzYxYzYyYzYzYzY0YzY1YzY2YzY3YzY4YzY5YzZhYzZi
YzZjYzZkYzZlYzZmYzc0YzQ1YzQ2YzQ3YzQ4YzQ5YzUwYzUxYzUyYzUzYzU0YzU1
QIDAQAB
-----END RSA PUBLIC KEY-----"""
    return {"public_key": mock_public_key}


def empty_paginated_response(key: str):
    """Create empty paginated response for any resource type."""
    return {key: [], "pages": {"page": 1, "total": 0, "num_pages": 1, "page_size": 20}}


@app.post("/v1/secrets/export")
async def export_secrets(export_params: Dict[str, Any]):
    """Mock endpoint for exporting secrets with encryption."""
    return empty_paginated_response("secrets")


@app.post("/v1/catalogs/export")
async def export_catalogs(export_params: Dict[str, Any]):
    """Mock endpoint for exporting catalogs with encryption."""
    return empty_paginated_response("catalogs")


@app.get("/v1/session")
async def get_session():
    """
    Mock endpoint for getting current session.

    IMPORTANT: This response format must match the OpenAPI-generated models in:
    - crates/tower-api/src/models/describe_session_response.rs
    - crates/tower-api/src/models/session.rs
    - crates/tower-api/src/models/user.rs
    - crates/tower-api/src/models/featurebase_identity.rs
    - crates/tower-api/src/models/team.rs
    - crates/tower-api/src/models/token.rs

    If integration tests fail with "UnknownDescribeSessionValue" errors after
    regenerating the API client, update this response to match the new schema.

    See tests/mock-api-server/README.md for debugging steps.
    """
    return {
        "session": {
            "featurebase_identity": {
                "company_hash": "mock_company_hash",
                "user_hash": "mock_user_hash",
            },
            "user": {
                # Fields below are required by crates/tower-api/src/models/user.rs
                # Missing any field may cause "UnknownDescribeSessionValue" errors
                "company": "Mock Company",
                "country": "US",
                "created_at": "2023-01-01T00:00:00Z",
                "email": "test@example.com",
                "first_name": "Test",
                "is_alerts_enabled": True,
                "is_confirmed": True,
                "is_invitation_claimed": True,
                "is_subscribed_to_changelog": False,
                "last_name": "User",
                "profile_photo_url": "https://example.com/photo.jpg",
            },
            "teams": [
                {"name": "default", "type": "user", "token": {"jwt": "mock_jwt_token"}}
            ],
            "token": {"jwt": "mock_jwt_token"},
        }
    }


@app.post("/v1/session/refresh")
async def refresh_session(refresh_params: Dict[str, Any] = None):
    """Mock endpoint for refreshing session."""
    return {
        "user": {"id": "mock_user_id", "email": "test@example.com"},
        "teams": [
            {"name": "default", "type": "user", "token": {"jwt": "mock_jwt_token"}}
        ],
        "active_team": {
            "name": "default",
            "type": "user",
            "token": {"jwt": "mock_jwt_token"},
        },
    }


NORMAL_LOG_ENTRIES = [
    (1, "Starting application...", "2025-08-22T12:00:00Z"),
    (2, "Hello, World!", "2025-08-22T12:00:01Z"),
    (3, "Application completed successfully", "2025-08-22T12:00:02Z"),
]


def make_log_data(seq: int, line_num: int, content: str, timestamp: str):
    return {
        "channel": "program",
        "content": content,
        "line_num": line_num,
        "reported_at": timestamp,
        "run_id": f"mock-run-{seq}",
    }


def make_log_event(seq: int, line_num: int, content: str, timestamp: str):
    return f"event: log\ndata: {json.dumps(make_log_data(seq, line_num, content, timestamp))}\n\n"


def make_warning_event(content: str, timestamp: str):
    data = {"data": {"content": content, "reported_at": timestamp}, "event": "warning"}
    return f"event: warning\ndata: {json.dumps(data)}\n\n"


@app.get("/v1/apps/{name}/runs/{seq}/logs")
async def describe_run_logs(name: str, seq: int):
    """Mock endpoint for getting run logs."""
    if name not in mock_apps_db:
        raise HTTPException(status_code=404, detail=f"App '{name}' not found")

    return {
        "log_lines": [
            make_log_data(seq, line_num, content, timestamp)
            for line_num, content, timestamp in NORMAL_LOG_ENTRIES
        ]
    }


async def generate_logs_after_completion_test_stream(seq: int):
    """Log before run completion, then log after.

    Timeline: Run completes at 1 second, second log sent at 1.5 seconds.
    """
    yield make_log_event(
        seq, 1, "First log before run completes", "2025-08-22T12:00:00Z"
    )
    await asyncio.sleep(1.5)
    yield make_log_event(
        seq, 2, "Second log after run completes", "2025-08-22T12:00:01Z"
    )


async def generate_warning_log_stream(seq: int):
    """Stream a warning and a couple of logs, then finish."""
    yield make_warning_event("Rate limit approaching", "2025-08-22T12:00:00Z")
    yield make_log_event(seq, 1, "Warning stream log 1", "2025-08-22T12:00:00Z")
    await asyncio.sleep(1.2)
    yield make_log_event(seq, 2, "Warning stream log 2", "2025-08-22T12:00:01Z")


async def generate_normal_log_stream(seq: int):
    """Normal log stream for regular tests."""
    for line_num, content, timestamp in NORMAL_LOG_ENTRIES:
        yield make_log_event(seq, line_num, content, timestamp)
        await asyncio.sleep(0.1)


@app.get("/v1/apps/{name}/runs/{seq}/logs/stream")
async def stream_run_logs(name: str, seq: int):
    """Mock endpoint for streaming run logs."""

    if name not in mock_apps_db:
        raise HTTPException(status_code=404, detail=f"App '{name}' not found")

    if "logs-warning" in name:
        stream = generate_warning_log_stream(seq)
    elif "logs-after-completion" in name:
        stream = generate_logs_after_completion_test_stream(seq)
    else:
        stream = generate_normal_log_stream(seq)

    return StreamingResponse(
        stream,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


# Schedule endpoints
@app.get("/v1/schedules")
async def list_schedules():
    """Mock endpoint for listing schedules."""
    return {
        "schedules": list(mock_schedules_db.values()),
        "pages": {
            "page": 1,
            "total": len(mock_schedules_db),
            "num_pages": 1,
            "page_size": 20,
        },
    }


@app.post("/v1/schedules")
async def create_schedule(schedule_data: Dict[str, Any]):
    """Mock endpoint for creating a schedule."""
    app_name = schedule_data.get("app_name")
    cron = schedule_data.get("cron")
    if not app_name or not cron:
        raise HTTPException(status_code=400, detail="app_name and cron are required")

    schedule_id = generate_id()
    new_schedule = create_schedule_object(
        schedule_id,
        app_name,
        cron,
        schedule_data.get("environment", "default"),
        schedule_data.get("parameters", []),
    )
    mock_schedules_db[schedule_id] = new_schedule
    return {"schedule": new_schedule}


@app.put("/v1/schedules/{schedule_id}")
async def update_schedule(schedule_id: str, schedule_data: Dict[str, Any]):
    """Mock endpoint for updating a schedule."""
    if schedule_id not in mock_schedules_db:
        raise HTTPException(
            status_code=404, detail=f"Schedule '{schedule_id}' not found"
        )

    schedule = mock_schedules_db[schedule_id]
    if "cron" in schedule_data:
        schedule["cron"] = schedule_data["cron"]
    if "parameters" in schedule_data:
        schedule["parameters"] = schedule_data["parameters"]
    schedule["updated_at"] = now_iso()

    return {"schedule": schedule}


@app.delete("/v1/schedules")
async def delete_schedule(schedule_data: Dict[str, Any]):
    """Mock endpoint for deleting schedules."""
    ids = schedule_data.get("ids", [])
    if not ids:
        raise HTTPException(status_code=400, detail="ids are required")

    deleted_schedules = [
        mock_schedules_db.pop(id) for id in ids if id in mock_schedules_db
    ]
    return {"schedules": deleted_schedules}


# Health check for testing
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.datetime.now().isoformat()}
