from collections import Counter
import pathlib
import sys
import tempfile
import unittest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
from tests.support import PYNIFLY_ROOT, SOURCE_ROOT as ANIMATED_SHIPS_ROOT
SOURCE_ROOT = ANIMATED_SHIPS_ROOT / "Distant"
sys.path.insert(0, str(PYNIFLY_ROOT))

from pyn.nifdefs import NiKeyType
from pyn.pynifly import NifFile
from ship_motion.nif_patch import patch_nif, route_timing_signature, route_value_signature, sha256_file
from ship_motion.profiles import classify_mesh


class NifPatchIntegrationTests(unittest.TestCase):
    def test_retimes_route_by_class_without_changing_values_or_structure(self):
        durations = {}
        heading_deltas = {}
        with tempfile.TemporaryDirectory() as temporary_directory:
            for filename, expected_keys in (("shiprowboat01.nif", 49), ("shiplongboat01.nif", 241), ("shiplarge01.nif", 385)):
                source = SOURCE_ROOT / filename
                before = NifFile(str(source))
                before_values = route_value_signature(before)
                before_nodes = set(before.nodes)
                before_shapes = Counter(shape.name for shape in before.shapes)
                output = pathlib.Path(temporary_directory) / filename
                result = patch_nif(source, output, classify_mesh("Distant", filename), PYNIFLY_ROOT)
                after = NifFile(str(output))
                data = after.nodes["SHIPBODY"].controller.interpolator.data
                after_values = route_value_signature(after)
                self.assertEqual(after_values["translations"], before_values["translations"])
                self.assertNotEqual(route_timing_signature(after), route_timing_signature(before))
                self.assertEqual((len(data.xrotations), len(data.yrotations), len(data.zrotations), len(data.translations)), (expected_keys, expected_keys, 0, expected_keys))
                self.assertEqual(set(after.nodes), before_nodes)
                self.assertEqual(Counter(shape.name for shape in after.shapes), before_shapes)
                self.assertEqual(sha256_file(source), result.source_sha256)
                self.assertEqual(result.base_z, float(before.nodes["SHIPBODY"].transform.translation[2]) + classify_mesh("Distant", filename).sink_offset_units)
                headings = [value for value, _, _ in after_values["zrotations"]]
                heading_deltas[filename] = max(abs(b-a) for a,b in zip(headings, headings[1:]))
                self.assertFalse(all(abs(forward) == 0.1 and abs(backward) == 0.1 for _, forward, backward in after_values["zrotations"]))
                durations[filename] = result.mapped_route_duration
            self.assertLess(durations["shiprowboat01.nif"], durations["shiplongboat01.nif"])
            self.assertLess(durations["shiplongboat01.nif"], durations["shiplarge01.nif"])
            self.assertGreater(heading_deltas["shiprowboat01.nif"], heading_deltas["shiplongboat01.nif"])
            self.assertGreater(heading_deltas["shiplongboat01.nif"], heading_deltas["shiplarge01.nif"])

    def test_rejects_same_source_and_destination(self):
        source = SOURCE_ROOT / "shiprowboat01.nif"
        with self.assertRaisesRegex(ValueError, "destination must differ from source"):
            patch_nif(source, source, classify_mesh("Distant", source.name), PYNIFLY_ROOT)

    def test_imperial_ship_has_dense_linear_inertial_course_without_route_changes(self):
        source = SOURCE_ROOT / "shiplargekatariah01Slow.nif"
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = pathlib.Path(temporary_directory) / source.name
            before = NifFile(str(source))
            before_route = before.root.controller.sequences["SpecialIdle"].controlled_blocks[0].interpolator.data
            before_values = [[float(v) for v in key.value] for key in before_route.translations]
            result = patch_nif(source, output, classify_mesh("Distant", source.name), PYNIFLY_ROOT)
            after = NifFile(str(output))
            after_route = after.root.controller.sequences["SpecialIdle"].controlled_blocks[0].interpolator.data
            after_values = [[float(v) for v in key.value] for key in after_route.translations]
            rotation_times = [float(key.time) for key in after_route.zrotations]
            self.assertEqual(after_values, before_values)
            self.assertEqual(len(after_route.translations), len(before_route.translations))
            self.assertEqual(after_route.properties.zRotations.interpolation, NiKeyType.LINEAR_KEY)
            self.assertGreaterEqual(len(after_route.zrotations), len(before_route.zrotations))
            self.assertLessEqual(max(b-a for a,b in zip(rotation_times, rotation_times[1:])), 0.501)
            self.assertLess(result.max_rotation_step_degrees, 10.0)
            self.assertGreater(result.route_rotation_key_count, 100)


if __name__ == "__main__":
    unittest.main()
