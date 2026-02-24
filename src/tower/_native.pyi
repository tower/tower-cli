def build_package(dir: str, output: str) -> None:
    """Build a Tower package from a directory containing a Towerfile.

    Native Rust implementation — see ``tower.packages.build_package`` for the
    full public API and documentation.

    Args:
        dir: Path to the directory that contains a ``Towerfile``.
        output: Destination path for the built ``.tar.gz`` archive.

    Raises:
        RuntimeError: If the build fails for any reason.
    """
    ...
def _run_cli(args: list[str]) -> None: ...
