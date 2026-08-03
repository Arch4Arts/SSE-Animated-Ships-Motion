import dataclasses
import math
import pathlib
import sys
import unittest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from ship_motion.curves import sample_motion
from ship_motion.profiles import MotionProfile, classify_mesh


class ProfileSelectionTests(unittest.TestCase):
    def test_selects_exact_motion_profiles(self):
        cases = [
            ("Distant", "shiprowboat01.nif", (6.0, 1.53333335, 7.0, 3.0, 1.5, 4.0, 12.0, 1.0)),
            ("NarrowPath", "shiprowboat01.nif", (4.5, 1.1, 5.2, 3.0, 1.5, 4.0, 12.0, 1.0)),
            ("Distant", "shiplongboat01.nif", (15.0, 1.62, 4.6666667, 7.5, 3.75, 12.0, 60.0, 1.25)),
            ("NarrowPath", "shiplongboat01.nif", (11.25, 1.17, 3.3333333, 7.5, 3.75, 12.0, 60.0, 1.25)),
            ("Distant", "shiplarge01.nif", (21.3333333, 1.3, 4.5, 16.0, 8.0, 32.0, 96.0, 2.0)),
            ("NarrowPath", "shiplarge01.nif", (14.6666667, 0.95, 3.3, 16.0, 8.0, 32.0, 96.0, 2.0)),
        ]
        for folder, filename, expected in cases:
            with self.subTest(folder=folder, filename=filename):
                self.assertEqual(dataclasses.astuple(classify_mesh(folder, filename))[:8], expected)

    def test_wreck_scales_only_amplitudes(self):
        profile = classify_mesh("NarrowPath", "shiplongboat01Wreck01.nif")
        self.assertEqual(
            dataclasses.astuple(profile)[:8],
            (11.25, 1.215, 3.5000000250000003, 7.5, 3.75, 12.0, 60.0, 1.25),
        )

    def test_rejects_unknown_folder(self):
        with self.assertRaisesRegex(ValueError, "unsupported route folder"):
            classify_mesh("UpDown", "shiplarge01.nif")

    def test_sink_offset_follow_hull_class(self):
        cases = [
            ("shiprowboat01.nif", 1, -19.0),
            ("shiplongboat01.nif", 2, -24.5),
            ("shiplarge01.nif", 3, 0.0),
            ("shiplongboat01Wreck01.nif", 2, -24.5),
        ]
        for filename, radius, sink in cases:
            with self.subTest(filename=filename):
                profile = classify_mesh("Distant", filename)
                self.assertEqual(profile.turn_smoothing_radius, radius)
                self.assertEqual(profile.sink_offset_units, sink)

    def test_v8_profiles_encode_mass_response(self):
        cases = [
            ("shiprowboat01.nif", (3.0, 4.0, 12.0, 45.0, 0.20, 1.5, 0.16, 0.14)),
            ("shiplongboat01.nif", (7.5, 12.0, 60.0, 55.0, 0.75, 3.75, 0.13, 0.11)),
            ("shiplarge01.nif", (16.0, 32.0, 96.0, 65.0, 2.50, 8.0, 0.08, 0.06)),
        ]
        for filename, expected in cases:
            with self.subTest(filename=filename):
                profile = classify_mesh("Distant", filename)
                self.assertEqual((profile.heave_pitch_period_seconds, profile.roll_period_seconds,
                                  profile.loop_duration_seconds, profile.pitch_phase_degrees,
                                  profile.pitch_smoothing_sigma_seconds, profile.harmonic_period_seconds,
                                  profile.heave_harmonic_weight, profile.pitch_harmonic_weight), expected)
        narrow_long = classify_mesh("NarrowPath", "shiplongboat01.nif")
        self.assertAlmostEqual(narrow_long.roll_degrees, 3.3333333)
        self.assertEqual(narrow_long.sink_offset_units, -24.5)

    def test_wreck_preserves_inertial_timing_and_sink(self):
        normal = classify_mesh("Distant", "shiplongboat01.nif")
        wreck = classify_mesh("Distant", "shiplongboat01Wreck01.nif")
        self.assertEqual(
            (wreck.yaw_sigma_seconds, wreck.turn_lookahead_segments,
             wreck.minimum_turn_speed, wreck.sink_offset_units),
            (normal.yaw_sigma_seconds, normal.turn_lookahead_segments,
             normal.minimum_turn_speed, normal.sink_offset_units),
        )
        self.assertEqual(
            (wreck.heave_pitch_period_seconds, wreck.harmonic_period_seconds,
             wreck.roll_period_seconds, wreck.loop_duration_seconds,
             wreck.pitch_phase_degrees, wreck.pitch_smoothing_sigma_seconds,
             wreck.heave_harmonic_weight, wreck.pitch_harmonic_weight),
            (normal.heave_pitch_period_seconds, normal.harmonic_period_seconds,
             normal.roll_period_seconds, normal.loop_duration_seconds,
             normal.pitch_phase_degrees, normal.pitch_smoothing_sigma_seconds,
             normal.heave_harmonic_weight, normal.pitch_harmonic_weight),
        )

    def test_folder_variants_share_timing_but_not_amplitude(self):
        for filename in ("shiprowboat01.nif", "shiplongboat01.nif", "shiplarge01.nif"):
            distant = classify_mesh("Distant", filename)
            narrow = classify_mesh("NarrowPath", filename)
            self.assertNotEqual((distant.heave_units, distant.pitch_degrees),
                                (narrow.heave_units, narrow.pitch_degrees))
            self.assertEqual(dataclasses.astuple(distant)[3:8], dataclasses.astuple(narrow)[3:8])


class MotionCurveTests(unittest.TestCase):
    def test_class_loops_close_with_expected_key_counts(self):
        for filename, count, stop in (
            ("shiprowboat01.nif", 33, 8.0),
            ("shiplongboat01.nif", 121, 30.0),
            ("shiplarge01.nif", 121, 30.0),
        ):
            with self.subTest(filename=filename):
                samples = sample_motion(classify_mesh("Distant", filename))
                self.assertEqual(len(samples), count)
                self.assertEqual(samples[-1].time, stop)
                self.assertEqual(samples[0], dataclasses.replace(samples[-1], time=0.0))
                self.assertTrue(all(sample.yaw_radians == 0.0 for sample in samples))

    def test_curves_reach_configured_amplitudes(self):
        profile = classify_mesh("Distant", "shiplongboat01.nif")
        samples = sample_motion(profile)
        self.assertAlmostEqual(max(abs(x.heave) for x in samples), 15.0, places=6)
        self.assertAlmostEqual(max(abs(x.pitch_radians) for x in samples), math.radians(1.62), places=6)
        self.assertAlmostEqual(max(abs(x.roll_radians) for x in samples), math.radians(4.6666667), places=6)

    def test_rejects_step_that_cannot_close_loop(self):
        with self.assertRaisesRegex(ValueError, "step must divide loop duration"):
            sample_motion(classify_mesh("Distant", "shiprowboat01.nif"), step=0.3)


if __name__ == "__main__":
    unittest.main()
