
import os
import httpx
import pytest

from tower.tower_api_client.models import (
    Run,
)

def test_running_apps(httpx_mock):
    # Mock the response from the API
    httpx_mock.add_response(
        method="POST",
        url="https://api.example.com/v1/apps/my-app/runs",
        json={
            "run": {
                "app_slug":     "my-app",
                "app_version":  "v6",
                "cancelled_at": None,
                "created_at":   "2025-04-25T20:54:58.762547Z",
                "ended_at":     "2025-04-25T20:55:35.220295Z",
                "environment":  "default",
                "number":       0,
                "run_id":       "50ac9bc1-c783-4359-9917-a706f20dc02c",
                "scheduled_at": "2025-04-25T20:54:58.761867Z",
                "started_at":   "2025-04-25T20:54:59.366937Z",
                "status":       "pending",
                "status_group": "",
                "parameters":   []
            }
        },
        status_code=200,
    )

    # We tell the client to use the mock server.
    os.environ["TOWER_URL"] = "https://api.example.com"
    os.environ["TOWER_API_KEY"] = "abc123"

    # Call the function that makes the API request
    import tower
    run: Run = tower.run_app("my-app", environment="production")

    # Assert the response
    assert run is not None

def test_waiting_for_a_run(httpx_mock):
    # Mock the response from the API
    httpx_mock.add_response(
        method="GET",
        url="https://api.example.com/v1/apps/my-app/runs/3",
        json={
            "run": {
                "app_slug":     "my-app",
                "app_version":  "v6",
                "cancelled_at": None,
                "created_at":   "2025-04-25T20:54:58.762547Z",
                "ended_at":     "2025-04-25T20:55:35.220295Z",
                "environment":  "default",
                "number":       3,
                "run_id":       "50ac9bc1-c783-4359-9917-a706f20dc02c",
                "scheduled_at": "2025-04-25T20:54:58.761867Z",
                "started_at":   "2025-04-25T20:54:59.366937Z",
                "status":       "pending",
                "status_group": "",
                "parameters":   []
            }
        },
        status_code=200,
    )

    # Second request, will indicate that it's done.
    httpx_mock.add_response(
        method="GET",
        url="https://api.example.com/v1/apps/my-app/runs/3",
        json={
            "run": {
                "app_slug":     "my-app",
                "app_version":  "v6",
                "cancelled_at": None,
                "created_at":   "2025-04-25T20:54:58.762547Z",
                "ended_at":     "2025-04-25T20:55:35.220295Z",
                "environment":  "default",
                "number":       3,
                "run_id":       "50ac9bc1-c783-4359-9917-a706f20dc02c",
                "scheduled_at": "2025-04-25T20:54:58.761867Z",
                "started_at":   "2025-04-25T20:54:59.366937Z",
                "status":       "exited",
                "status_group": "successful",
                "parameters":   []
            }
        },
        status_code=200,
    )

    # We tell the client to use the mock server.
    os.environ["TOWER_URL"] = "https://api.example.com"
    os.environ["TOWER_API_KEY"] = "abc123"

    import tower

    run = Run(
        app_slug="my-app",
        app_version="v6",
        cancelled_at=None,
        created_at="2025-04-25T20:54:58.762547Z",
        ended_at="2025-04-25T20:55:35.220295Z",
        environment="default",
        number=3,
        run_id="50ac9bc1-c783-4359-9917-a706f20dc02c",
        scheduled_at="2025-04-25T20:54:58.761867Z",
        started_at="2025-04-25T20:54:59.366937Z",
        status="crashed",
        status_group="failed",
        parameters=[]
    )

    # Set WAIT_TIMEOUT to 0 so we don't have to...wait.
    tower._client.WAIT_TIMEOUT = 0

    # Now actually wait for the run.
    tower.wait_for_run(run)

def test_waiting_for_multiple_runs(httpx_mock):
    # Mock the response from the API
    httpx_mock.add_response(
        method="GET",
        url="https://api.example.com/v1/apps/my-app/runs/3",
        json={
            "run": {
                "app_slug":     "my-app",
                "app_version":  "v6",
                "cancelled_at": None,
                "created_at":   "2025-04-25T20:54:58.762547Z",
                "ended_at":     "2025-04-25T20:55:35.220295Z",
                "environment":  "default",
                "number":       3,
                "run_id":       "50ac9bc1-c783-4359-9917-a706f20dc02c",
                "scheduled_at": "2025-04-25T20:54:58.761867Z",
                "started_at":   "2025-04-25T20:54:59.366937Z",
                "status":       "pending",
                "status_group": "",
                "parameters":   []
            }
        },
        status_code=200,
    )

    # Second request, will indicate that it's done.
    httpx_mock.add_response(
        method="GET",
        url="https://api.example.com/v1/apps/my-app/runs/3",
        json={
            "run": {
                "app_slug":     "my-app",
                "app_version":  "v6",
                "cancelled_at": None,
                "created_at":   "2025-04-25T20:54:58.762547Z",
                "ended_at":     "2025-04-25T20:55:35.220295Z",
                "environment":  "default",
                "number":       3,
                "run_id":       "50ac9bc1-c783-4359-9917-a706f20dc02c",
                "scheduled_at": "2025-04-25T20:54:58.761867Z",
                "started_at":   "2025-04-25T20:54:59.366937Z",
                "status":       "exited",
                "status_group": "successful",
                "parameters":   []
            }
        },
        status_code=200,
    )

    # Second request, will indicate that it's done.
    httpx_mock.add_response(
        method="GET",
        url="https://api.example.com/v1/apps/my-app/runs/4",
        json={
            "run": {
                "app_slug":     "my-app",
                "app_version":  "v6",
                "cancelled_at": None,
                "created_at":   "2025-04-25T20:54:58.762547Z",
                "ended_at":     "2025-04-25T20:55:35.220295Z",
                "environment":  "default",
                "number":       3,
                "run_id":       "50ac9bc1-c783-4359-9917-a706f20dc02c",
                "scheduled_at": "2025-04-25T20:54:58.761867Z",
                "started_at":   "2025-04-25T20:54:59.366937Z",
                "status":       "exited",
                "status_group": "successful",
                "parameters":   []
            }
        },
        status_code=200,
    )

    # We tell the client to use the mock server.
    os.environ["TOWER_URL"] = "https://api.example.com"
    os.environ["TOWER_API_KEY"] = "abc123"

    import tower

    run1 = Run(
        app_slug="my-app",
        app_version="v6",
        cancelled_at=None,
        created_at="2025-04-25T20:54:58.762547Z",
        ended_at="2025-04-25T20:55:35.220295Z",
        environment="default",
        number=3,
        run_id="50ac9bc1-c783-4359-9917-a706f20dc02c",
        scheduled_at="2025-04-25T20:54:58.761867Z",
        started_at="2025-04-25T20:54:59.366937Z",
        status="running",
        status_group="failed",
        parameters=[]
    )

    run2 = Run(
        app_slug="my-app",
        app_version="v6",
        cancelled_at=None,
        created_at="2025-04-25T20:54:58.762547Z",
        ended_at="2025-04-25T20:55:35.220295Z",
        environment="default",
        number=4,
        run_id="50ac9bc1-c783-4359-9917-a706f20dc02c",
        scheduled_at="2025-04-25T20:54:58.761867Z",
        started_at="2025-04-25T20:54:59.366937Z",
        status="running",
        status_group="failed",
        parameters=[]
    )

    # Set WAIT_TIMEOUT to 0 so we don't have to...wait.
    tower._client.WAIT_TIMEOUT = 0

    # Now actually wait for the run.
    tower.wait_for_runs([run1, run2])
