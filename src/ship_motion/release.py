from contextlib import contextmanager
from pathlib import Path
import subprocess
import tempfile

from .batch import build_patch, validate_patch


def _has_expected_routes(candidate: Path) -> bool:
    counts = {}
    for folder in ("Distant", "NarrowPath"):
        route_folder = candidate / folder
        counts[folder] = len([
            path for path in route_folder.glob("*.nif")
            if "base" not in path.name.casefold()
        ]) if route_folder.is_dir() else 0
    return counts == {"Distant": 22, "NarrowPath": 18}


def locate_mesh_root(root: Path) -> Path:
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f"input folder does not exist: {root}")
    candidates = [root]
    candidates.extend(path for path in root.rglob("*") if path.is_dir() and path.name.casefold() == "animatedship")
    matches = sorted({path.resolve() for path in candidates if _has_expected_routes(path)})
    if len(matches) != 1:
        raise ValueError(
            f"expected one unique Animated Ships mesh root with 22 Distant and "
            f"18 NarrowPath routes, found {len(matches)} under {root}"
        )
    return matches[0]


@contextmanager
def prepared_input(input_path: Path, seven_zip: Path, temporary_parent: Path | None = None):
    input_path = input_path.resolve()
    if input_path.is_dir():
        yield locate_mesh_root(input_path)
        return
    if not input_path.is_file():
        raise FileNotFoundError(f"input does not exist: {input_path}")
    seven_zip = seven_zip.resolve()
    if not seven_zip.is_file():
        raise FileNotFoundError(f"7-Zip executable does not exist: {seven_zip}")
    parent = temporary_parent.resolve() if temporary_parent else None
    if parent:
        parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="animated-ships-source-", dir=parent) as temporary_directory:
        extracted = Path(temporary_directory)
        subprocess.run(
            [str(seven_zip), "x", str(input_path), f"-o{extracted}", "-y"],
            check=True,
            capture_output=True,
            text=True,
        )
        yield locate_mesh_root(extracted)


def build_release(
    input_path: Path,
    output_path: Path,
    pynifly_root: Path,
    seven_zip: Path,
    archive_path: Path | None = None,
) -> dict[str, object]:
    output_path = output_path.resolve()
    archive_path = archive_path.resolve() if archive_path else None
    if output_path.exists():
        raise FileExistsError(f"output already exists: {output_path}")
    if archive_path and archive_path.exists():
        raise FileExistsError(f"archive already exists: {archive_path}")
    with prepared_input(input_path, seven_zip, output_path.parent) as source_root:
        summary = build_patch(source_root, output_path, pynifly_root)
        report = validate_patch(source_root, output_path, pynifly_root)
        if not report.valid:
            raise RuntimeError("release validation failed: " + "; ".join(report.errors))
    if archive_path:
        seven_zip = seven_zip.resolve()
        if not seven_zip.is_file():
            raise FileNotFoundError(f"7-Zip executable does not exist: {seven_zip}")
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [str(seven_zip), "a", "-t7z", str(archive_path), "Meshes", "-mx=9"],
            cwd=output_path,
            check=True,
            capture_output=True,
            text=True,
        )
    return {
        **summary,
        "valid": True,
        "meshes": report.meshes,
        "archive": str(archive_path) if archive_path else None,
    }
