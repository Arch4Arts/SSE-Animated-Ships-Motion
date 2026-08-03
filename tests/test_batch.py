import json
import pathlib
import sys
import tempfile
import unittest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
from tests.support import PYNIFLY_ROOT, SOURCE_ROOT

from ship_motion.batch import build_patch, discover_meshes, validate_patch


class BatchBuildIntegrationTests(unittest.TestCase):
    def test_discovers_exact_route_meshes(self):
        meshes = discover_meshes(SOURCE_ROOT)
        relative = [path.relative_to(SOURCE_ROOT) for path in meshes]
        self.assertEqual(len(meshes), 40)
        self.assertEqual(sum(path.parts[0] == "Distant" for path in relative), 22)
        self.assertEqual(sum(path.parts[0] == "NarrowPath" for path in relative), 18)
        self.assertFalse(any("UpDown" in path.parts or "LOD" in path.parts for path in relative))

    def test_builds_and_validates_standard_v8(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = pathlib.Path(temporary_directory) / "v4"
            summary = build_patch(SOURCE_ROOT, output, PYNIFLY_ROOT)
            report = validate_patch(SOURCE_ROOT, output, PYNIFLY_ROOT)
            self.assertEqual(summary, {"built": 40, "Distant": 22, "NarrowPath": 18, "failed": 0})
            self.assertTrue(report.valid, report.errors)
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual((manifest["version"], manifest["variant"]), (8, "standard"))
            self.assertEqual({entry["profile"]["yaw_sigma_seconds"] for entry in manifest["meshes"]}, {2.0, 6.0, 15.0})
            self.assertEqual({entry["profile"]["sink_offset_units"] for entry in manifest["meshes"]}, {-24.5, -19.0, 0.0})
            self.assertEqual(len(manifest["meshes"]), 40)
            self.assertEqual({entry["route_time_multiplier"] for entry in manifest["meshes"]}, {1.0, 1.25, 2.0})
            self.assertTrue(all(entry["yaw_key_count"] == 0 for entry in manifest["meshes"]))
            self.assertTrue(all(entry["route_rotation_key_count"] > 100 for entry in manifest["meshes"]))
            self.assertTrue(all(entry["max_rotation_step_degrees"] < 10.0 for entry in manifest["meshes"]))
            self.assertEqual(len(list(output.rglob("*.nif"))), 40)

    def test_refuses_existing_output(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = pathlib.Path(temporary_directory) / "existing"
            output.mkdir()
            with self.assertRaisesRegex(FileExistsError, "output already exists"):
                build_patch(SOURCE_ROOT, output, PYNIFLY_ROOT)


if __name__ == "__main__":
    unittest.main()
