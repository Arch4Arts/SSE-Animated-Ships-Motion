import pathlib
import subprocess
import tempfile
import unittest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from tests.support import PYNIFLY_ROOT, SOURCE_ROOT
from ship_motion.release import build_release, locate_mesh_root, prepared_input


SEVEN_ZIP = pathlib.Path(r"C:\Program Files\7-Zip\7z.exe")


def make_route_tree(root: pathlib.Path) -> pathlib.Path:
    mesh_root = root / "AnimatedShipsSE" / "00 Core Files" / "Meshes" / "Clutter" / "Vicn" / "AnimatedShip"
    for folder, count in (("Distant", 22), ("NarrowPath", 18)):
        target = mesh_root / folder
        target.mkdir(parents=True, exist_ok=True)
        for index in range(count):
            (target / f"route-{index:02}.nif").write_bytes(b"test")
    return mesh_root


class ReleaseInputTests(unittest.TestCase):
    def test_locates_nested_route_mesh_root(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            expected = make_route_tree(pathlib.Path(temporary_directory))
            self.assertEqual(locate_mesh_root(pathlib.Path(temporary_directory)), expected.resolve())

    def test_rejects_incomplete_source_tree(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            (root / "Distant").mkdir()
            (root / "NarrowPath").mkdir()
            with self.assertRaisesRegex(ValueError, "unique Animated Ships mesh root"):
                locate_mesh_root(root)

    @unittest.skipUnless(SEVEN_ZIP.exists(), "7-Zip is required for archive integration test")
    def test_extracts_archive_and_cleans_temporary_input(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            expected_source = make_route_tree(root / "source")
            archive = root / "Animated Ships.7z"
            subprocess.run(
                [str(SEVEN_ZIP), "a", str(archive), str(expected_source.parents[4])],
                check=True, capture_output=True, text=True,
            )
            extracted_root = None
            with prepared_input(archive, SEVEN_ZIP) as mesh_root:
                extracted_root = mesh_root
                self.assertTrue(mesh_root.exists())
                self.assertEqual(len(list(mesh_root.rglob("*.nif"))), 40)
            self.assertIsNotNone(extracted_root)
            self.assertFalse(extracted_root.exists())


class ReleaseBuildTests(unittest.TestCase):
    @unittest.skipUnless(SEVEN_ZIP.exists(), "7-Zip is required for release packaging test")
    def test_builds_validated_output_and_packages_only_meshes(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            output = root / "output"
            archive = root / "Animated Ships - Bobbing and Motion.7z"
            summary = build_release(SOURCE_ROOT, output, PYNIFLY_ROOT, SEVEN_ZIP, archive)
            self.assertEqual(summary["built"], 40)
            self.assertTrue(summary["valid"])
            self.assertEqual(summary["archive"], str(archive.resolve()))
            self.assertEqual(len(list((output / "Meshes").rglob("*.nif"))), 40)
            extracted = root / "release-contents"
            subprocess.run(
                [str(SEVEN_ZIP), "x", str(archive), f"-o{extracted}", "-y"],
                check=True, capture_output=True, text=True,
            )
            self.assertEqual(len(list((extracted / "Meshes").rglob("*.nif"))), 40)
            self.assertFalse((extracted / "manifest.json").exists())

    @unittest.skipUnless(SEVEN_ZIP.exists(), "7-Zip is required for archive input test")
    def test_builds_from_original_style_archive(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            source_wrapper = root / "source" / "AnimatedShipsSE" / "00 Core Files" / "Meshes" / "Clutter" / "Vicn"
            source_wrapper.mkdir(parents=True)
            link = source_wrapper / "AnimatedShip"
            # A junction avoids copying the large source tree before 7-Zip reads it.
            subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(SOURCE_ROOT)], check=True, capture_output=True, text=True)
            archive = root / "Animated Ships.7z"
            subprocess.run(
                [str(SEVEN_ZIP), "a", str(archive), str(root / "source" / "AnimatedShipsSE")],
                check=True, capture_output=True, text=True,
            )
            output = root / "output"
            summary = build_release(archive, output, PYNIFLY_ROOT, SEVEN_ZIP)
            self.assertEqual(summary["built"], 40)
            self.assertTrue(summary["valid"])
            self.assertIsNone(summary["archive"])


if __name__ == "__main__":
    unittest.main()
