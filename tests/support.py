import os
from pathlib import Path
import unittest


def dependency_path(variable: str) -> Path:
    value = os.environ.get(variable)
    if not value:
        raise unittest.SkipTest(f"set {variable} to run real-NIF integration tests")
    path = Path(value)
    if not path.exists():
        raise unittest.SkipTest(f"{variable} does not exist: {path}")
    return path


PYNIFLY_ROOT = dependency_path("PYNIFLY_ROOT")
SOURCE_ROOT = dependency_path("ANIMATED_SHIPS_MESH_ROOT")
