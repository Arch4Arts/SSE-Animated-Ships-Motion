import pathlib
import sys
import unittest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from ship_motion.route_timing import (
    build_time_map, curvature_strength, pchip_tangents,
    smooth_cyclic_headings, unwrap_headings, vertex_angles,
    interval_turn_angles, sample_inertial_headings, signed_vertex_turns,
)


class CurvatureTests(unittest.TestCase):
    def test_strength_uses_approved_control_points(self):
        cases = [(0, 0), (3, 0), (6.5, 0.25), (10, 0.5), (15, 0.75), (20, 1), (25, 1)]
        for angle, expected in cases:
            with self.subTest(angle=angle):
                self.assertAlmostEqual(curvature_strength(angle), expected)

    def test_vertex_angles_measure_real_turn(self):
        self.assertEqual(vertex_angles([(0, 0), (10, 0), (10, 10)]), [0.0, 90.0, 0.0])

    def test_unwrap_and_triangular_smoothing_preserve_winding(self):
        values = unwrap_headings([6.1, 0.1, 0.3])
        self.assertGreater(values[1], values[0])
        loop = [0.0, 0.0, 1.0, 0.0, 0.0]
        r1 = smooth_cyclic_headings(loop, 1)
        r2 = smooth_cyclic_headings(loop, 2)
        self.assertEqual(r1[-1] - r1[0], 0.0)
        self.assertLess(max(abs(b-a) for a,b in zip(r2,r2[1:])), max(abs(b-a) for a,b in zip(r1,r1[1:])))

    def test_pchip_tangents_are_monotone(self):
        tangents = pchip_tangents([0, 1, 2, 3], [0, 1, 1.5, 2])
        self.assertTrue(all(value >= 0 for value in tangents))


class TimeMapTests(unittest.TestCase):
    def test_signed_turns_and_lookahead_accumulate_small_bends(self):
        points = [(0, 0), (10, 0), (19.397, 3.420), (27.057, 9.848), (32.057, 18.508)]
        turns = signed_vertex_turns(points)
        self.assertEqual(len(turns), 5)
        self.assertTrue(all(15.0 < value < 25.0 for value in turns[1:4]))
        demand = interval_turn_angles(points, 3)
        self.assertGreater(demand[0], 50.0)

    def test_speed_envelope_uses_hand_checked_smoothstep(self):
        # Single 45-degree bend: smoothstep(0.5)=0.5, so rowboat speed is 0.875.
        mapping, stats = build_time_map([0, 10, 20], [(0, 0), (10, 0), (20, 10)], 1.0, 1, 0.75)
        self.assertAlmostEqual(stats.speed_factors[0], 0.875, places=3)
        self.assertAlmostEqual(mapping.new_times[1], 10 / 0.875, places=3)
        self.assertGreaterEqual(min(stats.speed_factors), 0.75)

    def test_speed_floor_depends_on_hull_class(self):
        points = [(0, 0), (10, 0), (0, 0.001)]
        for floor in (0.75, 0.65, 0.55):
            with self.subTest(floor=floor):
                _, stats = build_time_map([0, 10, 20], points, 1.0, 1, floor)
                self.assertGreaterEqual(min(stats.speed_factors), floor)
                self.assertAlmostEqual(min(stats.speed_factors), floor, places=3)

    def test_inertial_heading_keys_are_dense_smooth_and_mass_ordered(self):
        times = [0.0, 10.0, 20.0, 30.0, 40.0]
        headings = [0.0, 0.0, 3.141592653589793, 3.141592653589793, 0.0]
        maxima = []
        for sigma in (2.0, 6.0, 15.0):
            keys = sample_inertial_headings(times, headings, 40.0, sigma)
            self.assertLessEqual(max(b.time-a.time for a,b in zip(keys, keys[1:])), 0.5 + 1e-9)
            maximum = max(abs(b.value-a.value) for a,b in zip(keys, keys[1:]))
            self.assertLess(maximum, 0.18)  # below 10 degrees per key
            maxima.append(maximum)
            self.assertAlmostEqual(keys[-1].value - keys[0].value, 0.0, places=6)
        self.assertGreater(maxima[0], maxima[1])
        self.assertGreater(maxima[1], maxima[2])

    def test_new_parameter_validation(self):
        points = [(0, 0), (10, 0)]
        for lookahead, floor in ((0, 0.75), (1, 0.0), (1, 1.1)):
            with self.subTest(lookahead=lookahead, floor=floor):
                with self.assertRaises(ValueError):
                    build_time_map([0, 10], points, 1.0, lookahead, floor)
    def test_straight_route_uses_only_class_multiplier(self):
        points = [(0, 0), (10, 0), (20, 0)]
        for factor, expected in ((1, (0, 10, 20)), (1.25, (0, 12.5, 25)), (2, (0, 20, 40))):
            with self.subTest(factor=factor):
                mapping, stats = build_time_map([0, 10, 20], points, factor)
                self.assertEqual(mapping.new_times, expected)
                self.assertEqual(stats.max_turn_strength, 0.0)

    def test_sharp_turn_slows_before_then_recovers_after_turn(self):
        mapping, stats = build_time_map([0, 10, 20], [(0, 0), (10, 0), (10, 10)], 1.0)
        self.assertAlmostEqual(mapping.new_times[1], 15.0)
        self.assertLess(mapping.new_times[2] - mapping.new_times[1], 15.0)
        self.assertEqual(stats.max_turn_strength, 1.0)
        self.assertAlmostEqual(mapping.map_time(5), 7.5)

    def test_rejects_non_monotonic_times(self):
        with self.assertRaisesRegex(ValueError, "strictly increasing"):
            build_time_map([0, 10, 10], [(0, 0), (10, 0), (20, 0)], 1.0)

    def test_rejects_zero_length_segment(self):
        with self.assertRaisesRegex(ValueError, "zero-length"):
            build_time_map([0, 10, 20], [(0, 0), (0, 0), (20, 0)], 1.0)

    def test_rejects_mapping_outside_domain(self):
        mapping, _ = build_time_map([0, 10], [(0, 0), (10, 0)], 1.0)
        with self.assertRaisesRegex(ValueError, "outside time-map domain"):
            mapping.map_time(11)


if __name__ == "__main__":
    unittest.main()
