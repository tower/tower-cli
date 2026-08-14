import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from tower._dbt import (
    dbt,
    DbtCommand,
    DbtRunnerConfig,
    DbtWorkflow,
    parse_command_plan,
    load_profile_from_env,
    run_dbt_workflow,
    DEFAULT_COMMAND_PLAN,
)


@pytest.fixture
def temp_dbt_project():
    """Create a temporary dbt project directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir) / "test_project"
        project_path.mkdir()

        # Create minimal dbt_project.yml
        dbt_project_yml = project_path / "dbt_project.yml"
        dbt_project_yml.write_text(
            """
name: test_project
version: 1.0.0
profile: test
"""
        )

        yield project_path


@pytest.fixture
def sample_profile():
    """Sample dbt profile YAML content."""
    return """
test:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: test.db
"""


@pytest.fixture
def mock_dbt_runner():
    """Mock dbtRunner for testing without actual dbt execution."""
    mock_runner = MagicMock()
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.result = []
    mock_runner.invoke.return_value = mock_result
    return mock_runner


class TestDbtCommand:
    """Tests for DbtCommand class."""

    def test_dbt_command_creation(self):
        """Test creating a DbtCommand."""
        cmd = DbtCommand("build")
        assert cmd.name == "build"
        assert cmd.args == ()

    def test_dbt_command_with_args(self):
        """Test creating a DbtCommand with arguments."""
        cmd = DbtCommand("build", ("--select", "tag:daily"))
        assert cmd.name == "build"
        assert cmd.args == ("--select", "tag:daily")

    def test_dbt_command_from_tokens(self):
        """Test creating DbtCommand from token list."""
        cmd = DbtCommand.from_tokens(["build", "--select", "tag:daily"])
        assert cmd.name == "build"
        assert cmd.args == ("--select", "tag:daily")

    def test_dbt_command_from_tokens_empty(self):
        """Test that empty tokens raise ValueError."""
        with pytest.raises(ValueError, match="dbt command cannot be empty"):
            DbtCommand.from_tokens([])

    def test_dbt_command_to_arg_list(self):
        """Test converting DbtCommand to argument list."""
        cmd = DbtCommand("build", ("--select", "models/"))
        assert cmd.to_arg_list() == ["build", "--select", "models/"]


class TestParseCommandPlan:
    """Tests for parse_command_plan function."""

    def test_parse_single_command(self):
        """Test parsing a single command."""
        result = parse_command_plan("deps")
        assert len(result) == 1
        assert result[0].name == "deps"
        assert result[0].args == ()

    def test_parse_multiple_commands(self):
        """Test parsing multiple comma-separated commands."""
        result = parse_command_plan("deps, seed, build")
        assert len(result) == 3
        assert result[0].name == "deps"
        assert result[1].name == "seed"
        assert result[2].name == "build"

    def test_parse_commands_with_args(self):
        """Test parsing commands with arguments."""
        result = parse_command_plan(
            "deps, seed --full-refresh, build --select tag:daily"
        )
        assert len(result) == 3
        assert result[0].name == "deps"
        assert result[1].name == "seed"
        assert result[1].args == ("--full-refresh",)
        assert result[2].name == "build"
        assert result[2].args == ("--select", "tag:daily")

    def test_parse_commands_with_newlines(self):
        """Test parsing commands separated by newlines."""
        result = parse_command_plan("deps\nseed\nbuild")
        assert len(result) == 3

    def test_parse_empty_string(self):
        """Test that empty string returns default command plan."""
        result = parse_command_plan("")
        assert result == DEFAULT_COMMAND_PLAN

    def test_parse_none(self):
        """Test that None returns default command plan."""
        result = parse_command_plan(None)
        assert result == DEFAULT_COMMAND_PLAN

    def test_parse_whitespace_only(self):
        """Test that whitespace-only string returns default command plan."""
        result = parse_command_plan("   ,  , ")
        assert result == DEFAULT_COMMAND_PLAN


class TestLoadProfileFromEnv:
    """Tests for load_profile_from_env function."""

    def test_load_profile_from_default_env_var(self):
        """Test loading profile from default environment variable."""
        test_profile = "test: profile: content"
        with patch.dict(os.environ, {"DBT_PROFILE_YAML": test_profile}):
            result = load_profile_from_env()
            assert result == test_profile + "\n"

    def test_load_profile_from_custom_env_var(self):
        """Test loading profile from custom environment variable."""
        test_profile = "custom: profile: content"
        with patch.dict(os.environ, {"CUSTOM_PROFILE": test_profile}):
            result = load_profile_from_env("CUSTOM_PROFILE")
            assert result == test_profile + "\n"

    def test_load_profile_missing_env_var(self):
        """Test that missing environment variable raises RuntimeError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError, match="DBT_PROFILE_YAML is required"):
                load_profile_from_env()

    def test_load_profile_strips_trailing_whitespace(self):
        """Test that trailing whitespace is normalized."""
        test_profile = "test: profile  \n\n"
        with patch.dict(os.environ, {"DBT_PROFILE_YAML": test_profile}):
            result = load_profile_from_env()
            assert result == "test: profile\n"


class TestDbtRunnerConfig:
    """Tests for DbtRunnerConfig class."""

    def test_config_creation(self, temp_dbt_project, sample_profile):
        """Test creating a DbtRunnerConfig."""
        config = DbtRunnerConfig(
            project_path=temp_dbt_project,
            profile_payload=sample_profile,
        )
        assert config.project_path == temp_dbt_project
        assert config.profile_payload == sample_profile
        assert config.commands == DEFAULT_COMMAND_PLAN

    def test_config_converts_string_path(self, sample_profile):
        """Test that string paths are converted to Path objects."""
        config = DbtRunnerConfig(
            project_path="/tmp/test",
            profile_payload=sample_profile,
        )
        assert isinstance(config.project_path, Path)
        assert config.project_path == Path("/tmp/test")

    def test_config_custom_commands(self, temp_dbt_project, sample_profile):
        """Test config with custom commands."""
        custom_commands = (DbtCommand("build"),)
        config = DbtRunnerConfig(
            project_path=temp_dbt_project,
            profile_payload=sample_profile,
            commands=custom_commands,
        )
        assert config.commands == custom_commands

    def test_config_converts_list_to_tuple(self, temp_dbt_project, sample_profile):
        """Test that command lists are converted to tuples."""
        config = DbtRunnerConfig(
            project_path=temp_dbt_project,
            profile_payload=sample_profile,
            commands=[DbtCommand("build")],
        )
        assert isinstance(config.commands, tuple)


class TestDbtWorkflow:
    """Tests for DbtWorkflow class."""

    def test_workflow_creation(self, temp_dbt_project, sample_profile):
        """Test creating a DbtWorkflow."""
        config = DbtRunnerConfig(
            project_path=temp_dbt_project,
            profile_payload=sample_profile,
        )
        workflow = DbtWorkflow(config)
        assert workflow.config == config

    def test_workflow_has_run_method(self, temp_dbt_project, sample_profile):
        """Test that workflow has a run method."""
        config = DbtRunnerConfig(
            project_path=temp_dbt_project,
            profile_payload=sample_profile,
        )
        workflow = DbtWorkflow(config)
        assert hasattr(workflow, "run")
        assert callable(workflow.run)


class TestDbtFunction:
    """Tests for the main dbt() function."""

    def test_dbt_function_returns_workflow(self, temp_dbt_project, sample_profile):
        """Test that dbt() returns a DbtWorkflow."""
        workflow = dbt(
            project_path=temp_dbt_project,
            profile_payload=sample_profile,
        )
        assert isinstance(workflow, DbtWorkflow)

    def test_dbt_function_with_string_commands(self, temp_dbt_project, sample_profile):
        """Test dbt() with commands as a string."""
        workflow = dbt(
            project_path=temp_dbt_project,
            profile_payload=sample_profile,
            commands="deps,seed,build",
        )
        assert len(workflow.config.commands) == 3
        assert workflow.config.commands[0].name == "deps"

    def test_dbt_function_with_command_list(self, temp_dbt_project, sample_profile):
        """Test dbt() with commands as a list."""
        commands = [DbtCommand("build")]
        workflow = dbt(
            project_path=temp_dbt_project,
            profile_payload=sample_profile,
            commands=commands,
        )
        assert workflow.config.commands == tuple(commands)

    def test_dbt_function_with_none_commands(self, temp_dbt_project, sample_profile):
        """Test dbt() with None commands uses default."""
        workflow = dbt(
            project_path=temp_dbt_project,
            profile_payload=sample_profile,
            commands=None,
        )
        assert workflow.config.commands == DEFAULT_COMMAND_PLAN

    def test_dbt_function_with_full_refresh(self, temp_dbt_project, sample_profile):
        """Test dbt() with full_refresh option."""
        workflow = dbt(
            project_path=temp_dbt_project,
            profile_payload=sample_profile,
            full_refresh=True,
        )
        assert workflow.config.full_refresh is True

    def test_dbt_function_with_selector(self, temp_dbt_project, sample_profile):
        """Test dbt() with selector option."""
        workflow = dbt(
            project_path=temp_dbt_project,
            profile_payload=sample_profile,
            selector="tag:daily",
        )
        assert workflow.config.selector == "tag:daily"

    def test_dbt_has_helper_attributes(self):
        """Test that dbt function has helper attributes."""
        assert hasattr(dbt, "load_profile_from_env")
        assert hasattr(dbt, "parse_command_plan")
        assert hasattr(dbt, "DbtCommand")
        assert hasattr(dbt, "DbtRunnerConfig")
        assert hasattr(dbt, "run_dbt_workflow")


class TestRunDbtWorkflow:
    """Tests for run_dbt_workflow function."""

    def test_run_workflow_nonexistent_project(self, sample_profile):
        """Test that nonexistent project path raises FileNotFoundError."""
        config = DbtRunnerConfig(
            project_path="/nonexistent/path",
            profile_payload=sample_profile,
        )
        with pytest.raises(FileNotFoundError, match="dbt project path does not exist"):
            run_dbt_workflow(config)

    def test_run_workflow_success(
        self, temp_dbt_project, sample_profile, mock_dbt_runner
    ):
        """Test successful workflow execution."""
        with patch("tower._dbt.dbtRunner", return_value=mock_dbt_runner):
            config = DbtRunnerConfig(
                project_path=temp_dbt_project,
                profile_payload=sample_profile,
                commands=(DbtCommand("deps"),),
            )
            results = run_dbt_workflow(config)
            assert len(results) == 1
            assert mock_dbt_runner.invoke.called

    def test_run_workflow_with_selector(
        self, temp_dbt_project, sample_profile, mock_dbt_runner
    ):
        """Test workflow with selector adds --select flag."""
        with patch("tower._dbt.dbtRunner", return_value=mock_dbt_runner):
            config = DbtRunnerConfig(
                project_path=temp_dbt_project,
                profile_payload=sample_profile,
                commands=(DbtCommand("build"),),
                selector="tag:daily",
            )
            run_dbt_workflow(config)

            # Verify --select was added to invoke call
            call_args = mock_dbt_runner.invoke.call_args
            assert "--select" in call_args[0][0]
            assert "tag:daily" in call_args[0][0]

    def test_run_workflow_with_full_refresh(
        self, temp_dbt_project, sample_profile, mock_dbt_runner
    ):
        """Test workflow with full_refresh adds flag."""
        with patch("tower._dbt.dbtRunner", return_value=mock_dbt_runner):
            config = DbtRunnerConfig(
                project_path=temp_dbt_project,
                profile_payload=sample_profile,
                commands=(DbtCommand("build"),),
                full_refresh=True,
            )
            run_dbt_workflow(config)

            # Verify --full-refresh was added
            call_args = mock_dbt_runner.invoke.call_args
            assert "--full-refresh" in call_args[0][0]

    def test_run_workflow_with_vars(
        self, temp_dbt_project, sample_profile, mock_dbt_runner
    ):
        """Test workflow with vars adds --vars flag."""
        with patch("tower._dbt.dbtRunner", return_value=mock_dbt_runner):
            config = DbtRunnerConfig(
                project_path=temp_dbt_project,
                profile_payload=sample_profile,
                commands=(DbtCommand("build"),),
                vars_payload={"key": "value"},
            )
            run_dbt_workflow(config)

            # Verify --vars was added
            call_args = mock_dbt_runner.invoke.call_args
            assert "--vars" in call_args[0][0]

    def test_run_workflow_failure(self, temp_dbt_project, sample_profile):
        """Test workflow failure raises RuntimeError."""
        mock_runner = MagicMock()
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.message = "Command failed"
        mock_runner.invoke.return_value = mock_result

        with patch("tower._dbt.dbtRunner", return_value=mock_runner):
            config = DbtRunnerConfig(
                project_path=temp_dbt_project,
                profile_payload=sample_profile,
                commands=(DbtCommand("build"),),
            )
            with pytest.raises(RuntimeError, match="dbt command failed"):
                run_dbt_workflow(config)


class TestIntegrationWithTower:
    """Integration tests for tower.dbt() interface."""

    def test_tower_dbt_import(self):
        """Test that tower.dbt can be imported."""
        import tower

        assert hasattr(tower, "dbt")
        assert callable(tower.dbt)

    def test_tower_dbt_helper_functions(self):
        """Test that helper functions are accessible via tower.dbt."""
        import tower

        assert hasattr(tower.dbt, "load_profile_from_env")
        assert hasattr(tower.dbt, "parse_command_plan")
        assert hasattr(tower.dbt, "DbtCommand")
        assert hasattr(tower.dbt, "DbtRunnerConfig")
        assert callable(tower.dbt.load_profile_from_env)
        assert callable(tower.dbt.parse_command_plan)

    def test_tower_dbt_workflow_creation(self, temp_dbt_project, sample_profile):
        """Test creating a workflow via tower.dbt()."""
        import tower

        workflow = tower.dbt(
            project_path=temp_dbt_project,
            profile_payload=sample_profile,
            commands="deps",
        )
        assert isinstance(workflow, DbtWorkflow)
        assert hasattr(workflow, "run")

    def test_tower_dbt_parse_command_plan(self):
        """Test using tower.dbt.parse_command_plan."""
        import tower

        result = tower.dbt.parse_command_plan("deps,seed,build")
        assert len(result) == 3
        assert result[0].name == "deps"
