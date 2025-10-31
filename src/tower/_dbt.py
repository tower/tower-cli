from __future__ import annotations

import json
import logging
import os
import shlex
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping, MutableMapping, Sequence

from dbt.cli.main import dbtRunner

logger = logging.getLogger("tower.dbt")


@dataclass(frozen=True)
class DbtCommand:
    """Represents a dbt CLI command invocation."""

    name: str
    args: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_tokens(cls, tokens: Sequence[str]) -> "DbtCommand":
        if not tokens:
            raise ValueError("dbt command cannot be empty")
        return cls(name=tokens[0], args=tuple(tokens[1:]))

    def to_arg_list(self) -> list[str]:
        return [self.name, *self.args]


DEFAULT_COMMAND_PLAN: tuple[DbtCommand, ...] = (
    DbtCommand("deps"),
    DbtCommand("seed"),
    DbtCommand("build"),
)


def parse_command_plan(raw: str | None) -> tuple[DbtCommand, ...]:
    """
    Parse a comma or newline separated string into a command plan.

    Example input: "deps, seed --full-refresh, build --select tag:daily"
    """
    if not raw:
        return DEFAULT_COMMAND_PLAN
    pieces: list[str] = []
    for fragment in raw.replace("\n", ",").split(","):
        fragment = fragment.strip()
        if fragment:
            pieces.append(fragment)

    if not pieces:
        return DEFAULT_COMMAND_PLAN

    commands: list[DbtCommand] = []
    for fragment in pieces:
        tokens = shlex.split(fragment)
        commands.append(DbtCommand.from_tokens(tokens))
    return tuple(commands)


def load_profile_from_env(var_name: str = "DBT_PROFILE_YAML") -> str:
    payload = os.getenv(var_name)
    if not payload:
        raise RuntimeError(
            f"{var_name} is required. Provide the full profiles.yml contents via Tower secrets or environment variables."
        )
    return payload.rstrip() + "\n"


@dataclass
class DbtRunnerConfig:
    project_path: Path | str
    profile_payload: str
    commands: Sequence[DbtCommand] = DEFAULT_COMMAND_PLAN
    selector: str | None = None
    target: str | None = None
    threads: int | None = None
    vars_payload: Mapping[str, object] | str | None = None
    full_refresh: bool = False
    full_refresh_commands: Sequence[str] = ("seed", "run", "build")
    extra_env: Mapping[str, str] | None = None
    log_results: bool = True
    logger: logging.Logger = logger

    def __post_init__(self) -> None:
        if not isinstance(self.project_path, Path):
            self.project_path = Path(self.project_path)
        if not self.commands:
            self.commands = DEFAULT_COMMAND_PLAN
        if not isinstance(self.commands, tuple):
            self.commands = tuple(self.commands)
        if not isinstance(self.full_refresh_commands, tuple):
            self.full_refresh_commands = tuple(self.full_refresh_commands)


@contextmanager
def temporary_environ(overrides: Mapping[str, str]):
    original: MutableMapping[str, str | None] = {}
    for key, value in overrides.items():
        original[key] = os.environ.get(key)
        os.environ[key] = value
    try:
        yield
    finally:
        for key, previous in original.items():
            if previous is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = previous


def _serialise_vars(payload: Mapping[str, object] | str | None) -> str | None:
    if payload is None:
        return None
    if isinstance(payload, str):
        return payload
    return json.dumps(payload)


def _has_flag(args: list[str], flag: str) -> bool:
    for arg in args:
        if arg == flag or arg.startswith(f"{flag}="):
            return True
    return False


class DbtWorkflow:
    """A configured dbt workflow that can be executed."""

    def __init__(self, config: DbtRunnerConfig):
        self.config = config

    def run(self) -> list[object]:
        """Execute the dbt workflow."""
        return run_dbt_workflow(self.config)


def run_dbt_workflow(config: DbtRunnerConfig) -> list[object]:
    project_dir = config.project_path.resolve()
    if not project_dir.exists():
        raise FileNotFoundError(f"dbt project path does not exist: {project_dir}")

    runner = dbtRunner()
    results: list[object] = []

    with tempfile.TemporaryDirectory() as tmpdir:
        profiles_dir = Path(tmpdir)
        profile_path = profiles_dir / "profiles.yml"
        profile_path.write_text(config.profile_payload, encoding="utf-8")

        env_overrides = {"DBT_PROFILES_DIR": str(profiles_dir)}
        if config.extra_env:
            env_overrides.update(config.extra_env)

        with temporary_environ(env_overrides):
            runner_kwargs: dict[str, object] = {
                "project_dir": str(project_dir),
                "profiles_dir": str(profiles_dir),
            }
            if config.target:
                runner_kwargs["target"] = config.target
            if config.threads:
                runner_kwargs["threads"] = config.threads

            config.logger.info(
                "Starting dbt workflow | project=%s commands=%s target=%s selector=%s full_refresh=%s",
                project_dir,
                [cmd.name for cmd in config.commands],
                config.target or "<default>",
                config.selector or "<none>",
                config.full_refresh,
            )

            vars_payload = _serialise_vars(config.vars_payload)
            full_refresh_set = set(config.full_refresh_commands)

            for command in config.commands:
                args = command.to_arg_list()

                if config.selector and not (
                    _has_flag(args, "--select") or _has_flag(args, "-s")
                ):
                    args.extend(["--select", config.selector])

                if (
                    config.full_refresh
                    and command.name in full_refresh_set
                    and not _has_flag(args, "--full-refresh")
                ):
                    args.append("--full-refresh")

                if vars_payload and not _has_flag(args, "--vars"):
                    args.extend(["--vars", vars_payload])

                config.logger.info("Running dbt %s ...", " ".join(args))
                result = runner.invoke(args, **runner_kwargs)

                if config.log_results:
                    _log_run_results(config.logger, getattr(result, "result", None))

                if not result.success:
                    detail = getattr(result, "message", "") or str(
                        getattr(result, "exception", "")
                    )
                    config.logger.error(
                        "dbt command failed: %s | detail=%s", " ".join(args), detail
                    )
                    raise RuntimeError(f"dbt command failed: {' '.join(args)}")

                results.append(result)

            config.logger.info("dbt workflow finished successfully.")

    return results


def _log_run_results(log: logging.Logger, entries: Iterable[object] | None) -> None:
    if not entries:
        return
    for entry in entries:
        node = getattr(entry, "node", None)
        status = getattr(entry, "status", None)
        if node and hasattr(node, "name"):
            log.info("dbt result | %s -> %s", node.name, status)


def dbt(
    project_path: Path | str,
    profile_payload: str,
    commands: Sequence[DbtCommand] | str | None = None,
    selector: str | None = None,
    target: str | None = None,
    threads: int | None = None,
    vars_payload: Mapping[str, object] | str | None = None,
    full_refresh: bool = False,
    full_refresh_commands: Sequence[str] = ("seed", "run", "build"),
    extra_env: Mapping[str, str] | None = None,
    log_results: bool = True,
) -> DbtWorkflow:
    """
    Create a dbt workflow that can be executed.

    Args:
        project_path: Path to the dbt project root
        profile_payload: Full profiles.yml contents
        commands: Sequence of DbtCommand objects or a comma-separated string
        selector: Extra --select applied when commands don't already include one
        target: Target name from the profile (blank uses the profile default)
        threads: Number of threads to use
        vars_payload: Variables to pass to dbt (dict or JSON string)
        full_refresh: Whether to add --full-refresh flag
        full_refresh_commands: Commands that should receive --full-refresh
        extra_env: Additional environment variables
        log_results: Whether to log results

    Returns:
        A DbtWorkflow that can be executed with .run()

    Example:
        >>> workflow = tower.dbt(
        ...     project_path="path/to/dbt_project",
        ...     profile_payload=tower.dbt.load_profile_from_env("DBT_PROFILE_YAML"),
        ...     commands="deps,seed,build",
        ... )
        >>> results = workflow.run()
    """
    # Parse commands if provided as string
    if isinstance(commands, str):
        commands = parse_command_plan(commands)
    elif commands is None:
        commands = DEFAULT_COMMAND_PLAN

    config = DbtRunnerConfig(
        project_path=project_path,
        profile_payload=profile_payload,
        commands=commands,
        selector=selector,
        target=target,
        threads=threads,
        vars_payload=vars_payload,
        full_refresh=full_refresh,
        full_refresh_commands=full_refresh_commands,
        extra_env=extra_env,
        log_results=log_results,
    )
    return DbtWorkflow(config)


# Attach helper functions as attributes to the dbt function
dbt.load_profile_from_env = load_profile_from_env
dbt.parse_command_plan = parse_command_plan
dbt.DbtCommand = DbtCommand
dbt.DbtRunnerConfig = DbtRunnerConfig
dbt.run_dbt_workflow = run_dbt_workflow
