import gzip
import io
import json
import os
import tarfile
import tempfile

import pytest

_native = pytest.importorskip(
    "tower._native",
    reason="native extension not built (run: maturin develop --features pyo3)",
)


def _make_app(tmp_path, towerfile_content, files=None):
    """Create a minimal app directory with a Towerfile and optional source files."""
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    (app_dir / "Towerfile").write_text(towerfile_content)
    for name, content in (files or {}).items():
        path = app_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    return str(app_dir)


def _read_package(path):
    """Read a .tar.gz package and return a dict of {entry_path: content}."""
    with tarfile.open(path, "r:gz") as tar:
        entries = {}
        for member in tar.getmembers():
            if member.isfile():
                f = tar.extractfile(member)
                entries[member.name] = f.read().decode("utf-8") if f else ""
        return entries


SIMPLE_TOWERFILE = """\
[app]
name = "test-app"
script = "main.py"
source = ["*.py"]
"""


class TestBuildPackage:
    def test_produces_tar_gz(self, tmp_path):
        app_dir = _make_app(tmp_path, SIMPLE_TOWERFILE, {"main.py": "print('hello')"})
        output = str(tmp_path / "out.tar.gz")

        _native.build_package(app_dir, output)

        assert os.path.isfile(output)
        assert tarfile.is_tarfile(output)

    def test_contains_manifest(self, tmp_path):
        app_dir = _make_app(tmp_path, SIMPLE_TOWERFILE, {"main.py": "print('hello')"})
        output = str(tmp_path / "out.tar.gz")

        _native.build_package(app_dir, output)

        entries = _read_package(output)
        assert "MANIFEST" in entries

    def test_manifest_is_valid_json(self, tmp_path):
        app_dir = _make_app(tmp_path, SIMPLE_TOWERFILE, {"main.py": "print('hello')"})
        output = str(tmp_path / "out.tar.gz")

        _native.build_package(app_dir, output)

        entries = _read_package(output)
        manifest = json.loads(entries["MANIFEST"])
        assert manifest["invoke"] == "main.py"
        assert manifest["version"] == 3

    def test_contains_app_source_files(self, tmp_path):
        app_dir = _make_app(
            tmp_path,
            SIMPLE_TOWERFILE,
            {
                "main.py": "print('hello')",
                "utils.py": "x = 1",
            },
        )
        output = str(tmp_path / "out.tar.gz")

        _native.build_package(app_dir, output)

        entries = _read_package(output)
        assert "app/main.py" in entries
        assert "app/utils.py" in entries

    def test_contains_towerfile(self, tmp_path):
        app_dir = _make_app(tmp_path, SIMPLE_TOWERFILE, {"main.py": "print('hello')"})
        output = str(tmp_path / "out.tar.gz")

        _native.build_package(app_dir, output)

        entries = _read_package(output)
        assert "Towerfile" in entries

    def test_nested_source_files(self, tmp_path):
        towerfile = """\
[app]
name = "test-app"
script = "main.py"
source = ["*.py", "**/*.py"]
"""
        app_dir = _make_app(
            tmp_path,
            towerfile,
            {
                "main.py": "import pkg",
                "pkg/__init__.py": "",
                "pkg/module.py": "y = 2",
            },
        )
        output = str(tmp_path / "out.tar.gz")

        _native.build_package(app_dir, output)

        entries = _read_package(output)
        assert "app/main.py" in entries
        assert "app/pkg/__init__.py" in entries
        assert "app/pkg/module.py" in entries

    def test_manifest_contains_schedule(self, tmp_path):
        towerfile = """\
[app]
name = "scheduled-app"
script = "job.py"
source = ["*.py"]
schedule = "0 0 * * *"
"""
        app_dir = _make_app(tmp_path, towerfile, {"job.py": "print('run')"})
        output = str(tmp_path / "out.tar.gz")

        _native.build_package(app_dir, output)

        entries = _read_package(output)
        manifest = json.loads(entries["MANIFEST"])
        assert manifest["schedule"] == "0 0 * * *"

    def test_manifest_contains_parameters(self, tmp_path):
        towerfile = """\
[app]
name = "param-app"
script = "main.py"
source = ["*.py"]

[[parameters]]
name = "batch_size"
description = "Number of items per batch"
default = "100"
"""
        app_dir = _make_app(tmp_path, towerfile, {"main.py": "print('run')"})
        output = str(tmp_path / "out.tar.gz")

        _native.build_package(app_dir, output)

        entries = _read_package(output)
        manifest = json.loads(entries["MANIFEST"])
        assert len(manifest["parameters"]) == 1
        assert manifest["parameters"][0]["name"] == "batch_size"
        assert manifest["parameters"][0]["default"] == "100"

    def test_manifest_has_checksum(self, tmp_path):
        app_dir = _make_app(tmp_path, SIMPLE_TOWERFILE, {"main.py": "print('hello')"})
        output = str(tmp_path / "out.tar.gz")

        _native.build_package(app_dir, output)

        entries = _read_package(output)
        manifest = json.loads(entries["MANIFEST"])
        assert manifest.get("checksum")
        assert len(manifest["checksum"]) > 0

    def test_excludes_pycache(self, tmp_path):
        app_dir = _make_app(
            tmp_path,
            SIMPLE_TOWERFILE,
            {
                "main.py": "print('hello')",
                "__pycache__/main.cpython-311.pyc": "bytecode",
            },
        )
        output = str(tmp_path / "out.tar.gz")

        _native.build_package(app_dir, output)

        entries = _read_package(output)
        pycache_entries = [k for k in entries if "__pycache__" in k]
        assert pycache_entries == []

    def test_error_missing_towerfile(self, tmp_path):
        app_dir = str(tmp_path / "nonexistent")
        output = str(tmp_path / "out.tar.gz")

        with pytest.raises(RuntimeError):
            _native.build_package(app_dir, output)

    def test_error_invalid_towerfile(self, tmp_path):
        app_dir = _make_app(tmp_path, "this is not valid toml [[[", {"main.py": ""})
        output = str(tmp_path / "out.tar.gz")

        with pytest.raises(RuntimeError):
            _native.build_package(app_dir, output)

    def test_error_missing_app_name(self, tmp_path):
        towerfile = """\
[app]
script = "main.py"
"""
        app_dir = _make_app(tmp_path, towerfile, {"main.py": ""})
        output = str(tmp_path / "out.tar.gz")

        with pytest.raises(RuntimeError):
            _native.build_package(app_dir, output)
