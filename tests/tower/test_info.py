
import pytest
from tower import info


class TestIsCloudRun:
    def test_returns_true_when_set_to_true(self, monkeypatch):
        monkeypatch.setenv("TOWER__RUNTIME__IS_TOWER_MANAGED", "true")
        assert info.is_cloud_run() is True

    def test_returns_true_when_set_to_1(self, monkeypatch):
        monkeypatch.setenv("TOWER__RUNTIME__IS_TOWER_MANAGED", "1")
        assert info.is_cloud_run() is True

    def test_returns_true_when_set_to_yes(self, monkeypatch):
        monkeypatch.setenv("TOWER__RUNTIME__IS_TOWER_MANAGED", "yes")
        assert info.is_cloud_run() is True

    def test_returns_true_case_insensitive(self, monkeypatch):
        monkeypatch.setenv("TOWER__RUNTIME__IS_TOWER_MANAGED", "True")
        assert info.is_cloud_run() is True

    def test_returns_false_when_set_to_false(self, monkeypatch):
        monkeypatch.setenv("TOWER__RUNTIME__IS_TOWER_MANAGED", "false")
        assert info.is_cloud_run() is False

    def test_returns_false_when_set_to_0(self, monkeypatch):
        monkeypatch.setenv("TOWER__RUNTIME__IS_TOWER_MANAGED", "0")
        assert info.is_cloud_run() is False

    def test_returns_false_when_set_to_no(self, monkeypatch):
        monkeypatch.setenv("TOWER__RUNTIME__IS_TOWER_MANAGED", "no")
        assert info.is_cloud_run() is False

    def test_returns_false_when_env_var_missing(self, monkeypatch):
        monkeypatch.delenv("TOWER__RUNTIME__IS_TOWER_MANAGED", raising=False)
        assert info.is_cloud_run() is False

    def test_raises_on_invalid_value(self, monkeypatch):
        monkeypatch.setenv("TOWER__RUNTIME__IS_TOWER_MANAGED", "invalid")
        with pytest.raises(ValueError, match="invalid truth value"):
            info.is_cloud_run()


class TestIsLocal:
    def test_returns_true_when_set_to_true(self, monkeypatch):
        monkeypatch.setenv("TOWER__RUNTIME__IS_LOCAL", "true")
        assert info.is_local() is True

    def test_returns_true_when_set_to_1(self, monkeypatch):
        monkeypatch.setenv("TOWER__RUNTIME__IS_LOCAL", "1")
        assert info.is_local() is True

    def test_returns_true_when_set_to_yes(self, monkeypatch):
        monkeypatch.setenv("TOWER__RUNTIME__IS_LOCAL", "yes")
        assert info.is_local() is True

    def test_returns_true_case_insensitive(self, monkeypatch):
        monkeypatch.setenv("TOWER__RUNTIME__IS_LOCAL", "True")
        assert info.is_local() is True

    def test_returns_false_when_set_to_false(self, monkeypatch):
        monkeypatch.setenv("TOWER__RUNTIME__IS_LOCAL", "false")
        assert info.is_local() is False

    def test_returns_false_when_set_to_0(self, monkeypatch):
        monkeypatch.setenv("TOWER__RUNTIME__IS_LOCAL", "0")
        assert info.is_local() is False

    def test_returns_false_when_set_to_no(self, monkeypatch):
        monkeypatch.setenv("TOWER__RUNTIME__IS_LOCAL", "no")
        assert info.is_local() is False

    def test_returns_false_when_env_var_missing(self, monkeypatch):
        monkeypatch.delenv("TOWER__RUNTIME__IS_LOCAL", raising=False)
        assert info.is_local() is False

    def test_raises_on_invalid_value(self, monkeypatch):
        monkeypatch.setenv("TOWER__RUNTIME__IS_LOCAL", "invalid")
        with pytest.raises(ValueError, match="invalid truth value"):
            info.is_local()


class TestIsManualRun:
    def test_returns_true_when_set_to_true(self, monkeypatch):
        monkeypatch.setenv("TOWER__RUNTIME__IS_MANUAL_RUN", "true")
        assert info.is_manual_run() is True

    def test_returns_false_when_set_to_false(self, monkeypatch):
        monkeypatch.setenv("TOWER__RUNTIME__IS_MANUAL_RUN", "false")
        assert info.is_manual_run() is False

    def test_returns_false_when_env_var_missing(self, monkeypatch):
        monkeypatch.delenv("TOWER__RUNTIME__IS_MANUAL_RUN", raising=False)
        assert info.is_manual_run() is False


class TestIsScheduledRun:
    def test_returns_true_when_schedule_name_set(self, monkeypatch):
        monkeypatch.setenv("TOWER__RUNTIME__SCHEDULE_NAME", "daily-job")
        assert info.is_scheduled_run() is True

    def test_returns_false_when_schedule_name_missing(self, monkeypatch):
        monkeypatch.delenv("TOWER__RUNTIME__SCHEDULE_NAME", raising=False)
        assert info.is_scheduled_run() is False


class TestScheduleName:
    def test_returns_name_when_set(self, monkeypatch):
        monkeypatch.setenv("TOWER__RUNTIME__SCHEDULE_NAME", "daily-job")
        assert info.schedule_name() == "daily-job"

    def test_returns_none_when_missing(self, monkeypatch):
        monkeypatch.delenv("TOWER__RUNTIME__SCHEDULE_NAME", raising=False)
        assert info.schedule_name() is None


class TestScheduleId:
    def test_returns_id_when_set(self, monkeypatch):
        monkeypatch.setenv("TOWER__RUNTIME__SCHEDULE_ID", "sched-123")
        assert info.schedule_id() == "sched-123"

    def test_returns_none_when_missing(self, monkeypatch):
        monkeypatch.delenv("TOWER__RUNTIME__SCHEDULE_ID", raising=False)
        assert info.schedule_id() is None


class TestRunId:
    def test_returns_id_when_set(self, monkeypatch):
        monkeypatch.setenv("TOWER__RUNTIME__RUN_ID", "run-456")
        assert info.run_id() == "run-456"

    def test_returns_none_when_missing(self, monkeypatch):
        monkeypatch.delenv("TOWER__RUNTIME__RUN_ID", raising=False)
        assert info.run_id() is None


class TestRunNumber:
    def test_returns_number_when_set(self, monkeypatch):
        monkeypatch.setenv("TOWER__RUNTIME__RUN_NUMBER", "42")
        assert info.run_number() == 42

    def test_returns_none_when_missing(self, monkeypatch):
        monkeypatch.delenv("TOWER__RUNTIME__RUN_NUMBER", raising=False)
        assert info.run_number() is None


class TestHostname:
    def test_returns_hostname_when_set(self, monkeypatch):
        monkeypatch.setenv("TOWER__HOST", "my-host.example.com")
        assert info.hostname() == "my-host.example.com"

    def test_returns_none_when_missing(self, monkeypatch):
        monkeypatch.delenv("TOWER__HOST", raising=False)
        assert info.hostname() is None


class TestPort:
    def test_returns_port_when_set(self, monkeypatch):
        monkeypatch.setenv("TOWER__PORT", "8080")
        assert info.port() == 8080

    def test_returns_none_when_missing(self, monkeypatch):
        monkeypatch.delenv("TOWER__PORT", raising=False)
        assert info.port() is None


class TestRunnerName:
    def test_returns_name_when_set(self, monkeypatch):
        monkeypatch.setenv("TOWER__RUNTIME__RUNNER_NAME", "my-runner")
        assert info.runner_name() == "my-runner"

    def test_returns_empty_string_when_missing(self, monkeypatch):
        monkeypatch.delenv("TOWER__RUNTIME__RUNNER_NAME", raising=False)
        assert info.runner_name() == ""


class TestRunnerId:
    def test_returns_id_when_set(self, monkeypatch):
        monkeypatch.setenv("TOWER__RUNTIME__RUNNER_ID", "runner-789")
        assert info.runner_id() == "runner-789"

    def test_returns_empty_string_when_missing(self, monkeypatch):
        monkeypatch.delenv("TOWER__RUNTIME__RUNNER_ID", raising=False)
        assert info.runner_id() == ""


class TestAppName:
    def test_returns_name_when_set(self, monkeypatch):
        monkeypatch.setenv("TOWER__RUNTIME__APP_NAME", "my-app")
        assert info.app_name() == "my-app"

    def test_returns_empty_string_when_missing(self, monkeypatch):
        monkeypatch.delenv("TOWER__RUNTIME__APP_NAME", raising=False)
        assert info.app_name() == ""


class TestTeamName:
    def test_returns_name_when_set(self, monkeypatch):
        monkeypatch.setenv("TOWER__RUNTIME__TEAM_NAME", "my-team")
        assert info.team_name() == "my-team"

    def test_returns_empty_string_when_missing(self, monkeypatch):
        monkeypatch.delenv("TOWER__RUNTIME__TEAM_NAME", raising=False)
        assert info.team_name() == ""


class TestEnvironment:
    def test_returns_env_when_set(self, monkeypatch):
        monkeypatch.setenv("TOWER__RUNTIME__ENVIRONMENT_NAME", "production")
        assert info.environment() == "production"

    def test_returns_empty_string_when_missing(self, monkeypatch):
        monkeypatch.delenv("TOWER__RUNTIME__ENVIRONMENT_NAME", raising=False)
        assert info.environment() == ""
