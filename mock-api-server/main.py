from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import json
import datetime

app = FastAPI(
    title="Tower Mock API",
    description="A mock API server for Tower CLI testing.",
    version="1.0.0",
)

# In-memory data stores for mock responses
mock_apps_db = {}
mock_secrets_db = {}
mock_teams_db = {}
mock_runs_db = {}

# Helper to generate unique IDs
def generate_id():
    return str(datetime.datetime.now().timestamp()).replace(".", "")

@app.get("/")
async def read_root():
    return {"message": "Tower Mock API is running!"}

# Placeholder for /v1/apps endpoints
@app.get("/v1/apps")
async def list_apps():
    return {"apps": list(mock_apps_db.values()), "pages": {"page": 1, "total": len(mock_apps_db), "num_pages": 1, "page_size": 20}}

@app.post("/v1/apps")
async def create_app(app_data: Dict[str, Any]):
    app_name = app_data.get("name")
    if not app_name:
        raise HTTPException(status_code=400, detail="App name is required")
    if app_name in mock_apps_db:
        raise HTTPException(status_code=409, detail=f"App '{app_name}' already exists")

    new_app = {
        "name": app_name,
        "owner": "mock_owner",
        "short_description": app_data.get("short_description", ""),
        "version": "1.0.0",
        "schedule": None,
        "created_at": datetime.datetime.now().isoformat(),
        "next_run_at": None,
        "health_status": "healthy",
        "run_results": {
            "cancelled": 0, "crashed": 0, "errored": 0, "exited": 0, "pending": 0, "running": 0
        }
    }
    mock_apps_db[app_name] = new_app
    return {"app": new_app}

@app.get("/v1/apps/{name}")
async def describe_app(name: str):
    app_info = mock_apps_db.get(name)
    if not app_info:
        raise HTTPException(status_code=404, detail=f"App '{name}' not found")
    return {"app": app_info, "runs": []} # Simplistic, no runs yet

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
    version_num = "1.0.0" # Simplified versioning
    deployed_version = {
        "version": version_num,
        "parameters": [],
        "created_at": datetime.datetime.now().isoformat(),
        "towerfile": "mock_towerfile_content"
    }
    # Update app's version
    mock_apps_db[name]["version"] = version_num
    return {"version": deployed_version}

@app.post("/v1/apps/{name}/runs")
async def run_app(name: str, run_params: Dict[str, Any]):
    if name not in mock_apps_db:
        raise HTTPException(status_code=404, detail=f"App '{name}' not found")

    run_id = generate_id()
    new_run = {
        "$link": f"/runs/{run_id}",
        "run_id": run_id,
        "number": len(mock_runs_db) + 1,
        "app_name": name,
        "status": "running",
        "status_group": "",
        "parameters": [{"name": k, "value": v} for k, v in run_params.get("parameters", {}).items()],
        "environment": run_params.get("environment", "default"),
        "exit_code": None,
        "created_at": datetime.datetime.now().isoformat(),
        "scheduled_at": datetime.datetime.now().isoformat(),
        "cancelled_at": None,
        "started_at": datetime.datetime.now().isoformat(),
        "ended_at": None,
        "app_version": mock_apps_db[name].get("version", "1.0.0")
    }
    mock_runs_db[run_id] = new_run
    return {"run": new_run}

# Placeholder for /secrets endpoints
@app.get("/v1/secrets")
async def list_secrets():
    return {"secrets": list(mock_secrets_db.values()), "pages": {"page": 1, "total": len(mock_secrets_db), "num_pages": 1, "page_size": 20}}

@app.post("/v1/secrets")
async def create_secret(secret_data: Dict[str, Any]):
    secret_name = secret_data.get("name")
    environment = secret_data.get("environment", "default")
    key = f"{environment}/{secret_name}"
    if not secret_name:
        raise HTTPException(status_code=400, detail="Secret name is required")
    if key in mock_secrets_db:
        raise HTTPException(status_code=409, detail=f"Secret '{secret_name}' in environment '{environment}' already exists")

    new_secret = {
        "name": secret_name,
        "environment": environment,
        "preview": secret_data.get("preview", "******"),
        "created_at": datetime.datetime.now().isoformat()
    }
    mock_secrets_db[key] = new_secret
    return {"secret": new_secret}

@app.delete("/v1/secrets/{name}")
async def delete_secret(name: str, environment: str = "default"):
    key = f"{environment}/{name}"
    if key not in mock_secrets_db:
        raise HTTPException(status_code=404, detail=f"Secret '{name}' in environment '{environment}' not found")
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
        raise HTTPException(status_code=409, detail=f"Team '{team_name}' already exists")

    new_team = {
        "name": team_name,
        "type": "team",
        "token": {"jwt": "mock_jwt_token"}
    }
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

@app.post("/v1/session/refresh")
async def refresh_session(refresh_params: Dict[str, Any] = None):
    """Mock endpoint for refreshing session."""
    return {
        "user": {
            "id": "mock_user_id",
            "email": "test@example.com"
        },
        "teams": [
            {
                "name": "default",
                "type": "user",
                "token": {"jwt": "mock_jwt_token"}
            }
        ],
        "active_team": {
            "name": "default",
            "type": "user",
            "token": {"jwt": "mock_jwt_token"}
        }
    }

@app.get("/v1/apps/{name}/runs/{seq}/logs")
async def describe_run_logs(name: str, seq: int):
    """Mock endpoint for getting run logs."""
    if name not in mock_apps_db:
        raise HTTPException(status_code=404, detail=f"App '{name}' not found")
    
    # Return mock log entries
    return {
        "log_lines": [
            {"timestamp": "2025-08-22T12:00:00Z", "message": "Starting application..."},
            {"timestamp": "2025-08-22T12:00:01Z", "message": "Hello, World!"},
            {"timestamp": "2025-08-22T12:00:02Z", "message": "Application completed successfully"}
        ]
    }

# Health check for testing
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.datetime.now().isoformat()}
