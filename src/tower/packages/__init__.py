from .._native import build_package as _native_build_package


def build_package(dir: str, output: str) -> None:
    """Build a Tower package from a directory containing a Towerfile.

    Compiles the application defined by the ``Towerfile`` in *dir* into a
    compressed ``.tar.gz`` archive and writes it to *output*.  The build
    pipeline runs natively via the ``tower_package`` Rust crate so it is
    fast and does not require Python-side dependency resolution.

    How it works:

    1. **Towerfile Discovery** — reads the ``Towerfile`` found in *dir* to
       build a ``PackageSpec`` (app name, entry-point script, source globs,
       optional schedule, parameters, …).
    2. **Native Resolution** — the ``tower_package`` Rust crate resolves
       source-file globs and assembles the package manifest (``MANIFEST``
       JSON) including a content checksum.
    3. **Tokio Runtime** — an embedded async Rust runtime handles concurrent
       file I/O and any network operations required during the build.
    4. **Artifact Generation** — source files are staged in a temporary build
       directory, compressed into a ``.tar.gz`` archive, and copied to
       *output*.

    Args:
        dir: Path to the directory that contains your ``Towerfile``.
        output: Destination path for the built ``.tar.gz`` package
            (e.g. ``"./dist/app_v1.tar.gz"``).

    Raises:
        RuntimeError: If *dir* does not exist, no ``Towerfile`` is found,
            the ``Towerfile`` is invalid TOML or is missing required fields
            (e.g. ``app.name``), or the native build pipeline fails for any
            other reason.

    Example::

        import tower

        try:
            tower.packages.build_package(
                dir="./projects/my-app",
                output="./dist/app_v1.tar.gz",
            )
            print("Build successful!")
        except RuntimeError as e:
            print(f"Build failed: {e}")
    """
    _native_build_package(dir, output)
