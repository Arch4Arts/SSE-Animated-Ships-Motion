from dataclasses import dataclass, replace
import math

from .profiles import MotionProfile


@dataclass(frozen=True)
class MotionSample:
    time: float
    heave: float
    pitch_radians: float
    roll_radians: float
    yaw_radians: float = 0.0


def _normalize(values: list[float], amplitude: float) -> list[float]:
    maximum = max(abs(value) for value in values)
    return [value * amplitude / maximum for value in values]


def sample_motion(profile: MotionProfile, step: float = 0.25) -> list[MotionSample]:
    duration = profile.loop_duration_seconds
    if step <= 0.0 or not math.isclose(duration / step, round(duration / step)):
        raise ValueError("step must divide loop duration")
    times = [index * step for index in range(round(duration / step) + 1)]
    primary = profile.heave_pitch_period_seconds
    harmonic = profile.harmonic_period_seconds
    heave_raw = [
        math.sin(2 * math.pi * time / primary)
        + 0.16 * math.sin(2 * math.pi * time / harmonic + 0.35)
        for time in times
    ]
    pitch_raw = [
        math.sin(2 * math.pi * time / primary + math.pi / 3)
        + 0.14 * math.sin(2 * math.pi * time / harmonic + 1.10)
        for time in times
    ]
    roll_raw = [
        math.sin(2 * math.pi * time / profile.roll_period_seconds + 0.85)
        + 0.10 * math.sin(2 * math.pi * time / harmonic + 2.20)
        for time in times
    ]
    heave = _normalize(heave_raw, profile.heave_units)
    pitch = _normalize(pitch_raw, math.radians(profile.pitch_degrees))
    roll = _normalize(roll_raw, math.radians(profile.roll_degrees))
    samples = [MotionSample(t, h, p, r) for t, h, p, r in zip(times, heave, pitch, roll)]
    samples[-1] = replace(samples[0], time=duration)
    return samples
