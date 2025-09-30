import os
import pytest
from datetime import datetime
from typing import List, Dict, Any, Optional

from tower.tower_api_client.models import Run
from tower.exceptions import RunFailedError


@pytest.fixture
def mock_api_config():
    """Configure the Tower API client to use mock server."""
    os.environ["TOWER_URL"] = "https://api.example.com"
    os.environ["TOWER_API_KEY"] = "abc123"

    # Only import after environment is configured
    import tower

    # Set WAIT_TIMEOUT to 0 to avoid actual waiting in tests
    tower._client.WAIT_TIMEOUT = 0

    return tower


@pytest.fixture
def mock_run_response_factory():
    """Factory to create consistent run response objects."""

    def _create_run_response(
        app_version: str = "v6",
        number: int = 0,
        run_id: str = "50ac9bc1-c783-4359-9917-a706f20dc02c",
        status: str = "pending",
        status_group: str = "",
        parameters: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Create a mock run response with the given parameters."""
        if parameters is None:
            parameters = []

        return {
            "run": {
                "$link": f"https://api.example.com/v1/apps/my-app/runs/{number}",
                "app_name": "my-app",
                "app_version": app_version,
                "cancelled_at": None,
                "created_at": "2025-04-25T20:54:58.762547Z",
                "ended_at": "2025-04-25T20:55:35.220295Z",
                "environment": "default",
                "number": number,
                "run_id": run_id,
                "scheduled_at": "2025-04-25T20:54:58.761867Z",
                "started_at": "2025-04-25T20:54:59.366937Z",
                "status": status,
                "exit_code": None,
                "status_group": status_group,
                "parameters": parameters,
            }
        }

    return _create_run_response


@pytest.fixture
def create_run_object():
    """Factory to create Run objects for testing."""

    def _create_run(
        app_version: str = "v6",
        number: int = 0,
        run_id: str = "50ac9bc1-c783-4359-9917-a706f20dc02c",
        status: str = "running",
        status_group: str = "failed",
        parameters: Optional[List[Dict[str, Any]]] = None,
    ) -> Run:
        """Create a Run object with the given parameters."""
        if parameters is None:
            parameters = []

        return Run(
            link="https://api.example.com/v1/apps/my-app/runs/0",
            app_name="my-app",
            exit_code=None,
            app_version=app_version,
            cancelled_at=None,
            created_at="2025-04-25T20:54:58.762547Z",
            ended_at="2025-04-25T20:55:35.220295Z",
            environment="default",
            number=number,
            run_id=run_id,
            scheduled_at="2025-04-25T20:54:58.761867Z",
            started_at="2025-04-25T20:54:59.366937Z",
            status=status,
            status_group=status_group,
            parameters=parameters,
        )

    return _create_run


def test_running_apps(httpx_mock, mock_api_config, mock_run_response_factory):
    # Mock the response from the API
    httpx_mock.add_response(
        method="POST",
        url="https://api.example.com/v1/apps/my-app/runs",
        json=mock_run_response_factory(),
        status_code=201,
    )

    # Call the function that makes the API request
    tower = mock_api_config
    run: Run = tower.run_app("my-app", environment="production")

    # Assert the response
    assert run is not None
    assert run.status == "pending"


def test_waiting_for_a_run(
    httpx_mock, mock_api_config, mock_run_response_factory, create_run_object
):
    run_number = 3

    # First response: pending status
    httpx_mock.add_response(
        method="GET",
        url=f"https://api.example.com/v1/apps/my-app/runs/{run_number}",
        json=mock_run_response_factory(number=run_number, status="pending"),
        status_code=200,
    )

    # Second response: completed status
    httpx_mock.add_response(
        method="GET",
        url=f"https://api.example.com/v1/apps/my-app/runs/{run_number}",
        json=mock_run_response_factory(
            number=run_number, status="exited", status_group="successful"
        ),
        status_code=200,
    )

    tower = mock_api_config
    run = create_run_object(number=run_number, status="pending")

    # Now actually wait for the run
    final_run = tower.wait_for_run(run)

    # Verify the final state
    assert final_run.status == "exited"
    assert final_run.status_group == "successful"


@pytest.mark.parametrize("run_numbers", [(3, 4)])
def test_waiting_for_multiple_runs(
    httpx_mock,
    mock_api_config,
    mock_run_response_factory,
    create_run_object,
    run_numbers,
):
    tower = mock_api_config
    runs = []

    # Setup mocks for each run
    for run_number in run_numbers:
        # First response: pending status
        httpx_mock.add_response(
            method="GET",
            url=f"https://api.example.com/v1/apps/my-app/runs/{run_number}",
            json=mock_run_response_factory(number=run_number, status="pending"),
            status_code=200,
        )

        # Second response: completed status
        httpx_mock.add_response(
            method="GET",
            url=f"https://api.example.com/v1/apps/my-app/runs/{run_number}",
            json=mock_run_response_factory(
                number=run_number, status="exited", status_group="successful"
            ),
            status_code=200,
        )

        # Create the Run object
        runs.append(create_run_object(number=run_number))

    # Now actually wait for the runs
    successful_runs, failed_runs = tower.wait_for_runs(runs)

    assert len(failed_runs) == 0

    # Verify all runs completed successfully
    for run in successful_runs:
        assert run.status == "exited"
        assert run.status_group == "successful"


def test_failed_runs_in_the_list(
    httpx_mock, mock_api_config, mock_run_response_factory, create_run_object
):
    tower = mock_api_config
    runs = []

    # For the first run, we're going to simulate a success.
    httpx_mock.add_response(
        method="GET",
        url=f"https://api.example.com/v1/apps/my-app/runs/1",
        json=mock_run_response_factory(number=1, status="pending"),
        status_code=200,
    )

    httpx_mock.add_response(
        method="GET",
        url=f"https://api.example.com/v1/apps/my-app/runs/1",
        json=mock_run_response_factory(
            number=1, status="exited", status_group="successful"
        ),
        status_code=200,
    )

    runs.append(create_run_object(number=1))

    # Second run will have been a failure.
    httpx_mock.add_response(
        method="GET",
        url=f"https://api.example.com/v1/apps/my-app/runs/2",
        json=mock_run_response_factory(number=2, status="pending"),
        status_code=200,
    )

    httpx_mock.add_response(
        method="GET",
        url=f"https://api.example.com/v1/apps/my-app/runs/2",
        json=mock_run_response_factory(
            number=2, status="crashed", status_group="failed"
        ),
        status_code=200,
    )

    runs.append(create_run_object(number=2))

    # Third run was a success.
    httpx_mock.add_response(
        method="GET",
        url=f"https://api.example.com/v1/apps/my-app/runs/3",
        json=mock_run_response_factory(number=3, status="pending"),
        status_code=200,
    )

    httpx_mock.add_response(
        method="GET",
        url=f"https://api.example.com/v1/apps/my-app/runs/3",
        json=mock_run_response_factory(
            number=3, status="exited", status_group="successful"
        ),
        status_code=200,
    )

    runs.append(create_run_object(number=3))

    # Now actually wait for the runs
    successful_runs, failed_runs = tower.wait_for_runs(runs)

    assert len(failed_runs) == 1

    # Verify all successful runs
    for run in successful_runs:
        assert run.status == "exited"
        assert run.status_group == "successful"

    # Verify all failed
    for run in failed_runs:
        assert run.status == "crashed"
        assert run.status_group == "failed"


def test_raising_an_error_during_partial_failure(
    httpx_mock, mock_api_config, mock_run_response_factory, create_run_object
):
    tower = mock_api_config
    runs = []

    # For the first run, we're going to simulate a success.
    httpx_mock.add_response(
        method="GET",
        url=f"https://api.example.com/v1/apps/my-app/runs/1",
        json=mock_run_response_factory(number=1, status="pending"),
        status_code=200,
    )

    httpx_mock.add_response(
        method="GET",
        url=f"https://api.example.com/v1/apps/my-app/runs/1",
        json=mock_run_response_factory(
            number=1, status="exited", status_group="successful"
        ),
        status_code=200,
    )

    runs.append(create_run_object(number=1))

    # Second run will have been a failure.
    httpx_mock.add_response(
        method="GET",
        url=f"https://api.example.com/v1/apps/my-app/runs/2",
        json=mock_run_response_factory(number=2, status="pending"),
        status_code=200,
    )

    httpx_mock.add_response(
        method="GET",
        url=f"https://api.example.com/v1/apps/my-app/runs/2",
        json=mock_run_response_factory(
            number=2, status="crashed", status_group="failed"
        ),
        status_code=200,
    )

    runs.append(create_run_object(number=2))

    # Third run was a success.
    httpx_mock.add_response(
        method="GET",
        url=f"https://api.example.com/v1/apps/my-app/runs/3",
        json=mock_run_response_factory(number=3, status="pending"),
        status_code=200,
    )

    # NOTE: We don't have a second response for this run because we'll never
    # get to it.

    runs.append(create_run_object(number=3))

    # Now actually wait for the runs
    with pytest.raises(RunFailedError) as excinfo:
        tower.wait_for_runs(runs, raise_on_failure=True)


def test_raising_an_error_for_a_not_found_app(
    httpx_mock, mock_api_config, mock_run_response_factory, create_run_object
):
    tower = mock_api_config

    # Mock a 404 response with error model
    error_response = {
        "$schema": "https://api.tower.dev/v1/schemas/ErrorModel.json",
        "status": 404,
        "title": "Not Found",
        "detail": "The requested app 'non-existent-app' was not found",
        "instance": "https://api.example.com/v1/apps/non-existent-app",
        "type": "about:blank",
    }

    httpx_mock.add_response(
        method="POST",
        url="https://api.example.com/v1/apps/non-existent-app/runs",
        json=error_response,
        status_code=404,
    )

    # Attempt to run a non-existent app and verify it raises the correct error
    with pytest.raises(tower.exceptions.AppNotFoundError) as excinfo:
        tower.run_app("non-existent-app")

    assert "not found" in str(excinfo.value).lower()


def test_raising_an_unexpected_error_based_on_status_code(
    httpx_mock, mock_api_config, mock_run_response_factory, create_run_object
):
    tower = mock_api_config

    # Mock a 404 response with error model
    error_response = {
        "$schema": "https://api.tower.dev/v1/schemas/ErrorModel.json",
        "status": 404,
        "title": "Not Found",
        "detail": "The requested app 'non-existent-app' was not found",
        "instance": "https://api.example.com/v1/apps/non-existent-app",
        "type": "about:blank",
    }

    httpx_mock.add_response(
        method="POST",
        url="https://api.example.com/v1/apps/non-existent-app/runs",
        json=error_response,
        status_code=400,
    )

    # Attempt to run a non-existent app and verify it raises the correct error
    with pytest.raises(tower.exceptions.UnknownException) as excinfo:
        tower.run_app("non-existent-app")

    assert "unexpected status code" in str(excinfo.value).lower()
