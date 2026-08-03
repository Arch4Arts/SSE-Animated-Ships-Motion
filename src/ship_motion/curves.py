from dataclasses import dataclass
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


def _cyclic_gaussian(values: list[float], sigma_seconds: float, step: float) -> list[float]:
    if not values or sigma_seconds <= 0.0 or step <= 0.0:
        raise ValueError("cyclic Gaussian requires values, positive sigma, and positive step")
    radius = max(1, math.ceil(3.0 * sigma_seconds / step))
    offsets = range(-radius, radius + 1)
    weights = [math.exp(-0.5 * ((offset * step) / sigma_seconds) ** 2)
               for offset in offsets]
    normalizer = sum(weights)
    count = len(values)
    return [
        sum(weight * values[(index + offset) % count]
            for offset, weight in zip(offsets, weights)) / normalizer
        for index in range(count)
    ]


def sample_motion(profile: MotionProfile, step: float = 0.25) -> list[MotionSample]:
    duration = profile.loop_duration_seconds
    if step <= 0.0 or not math.isclose(duration / step, round(duration / step)):
        raise ValueError("step must divide loop duration")
    periods = (profile.heave_pitch_period_seconds, profile.harmonic_period_seconds,
               profile.roll_period_seconds)
    if (duration <= 0.0 or any(period <= 0.0 for period in periods)
            or profile.pitch_smoothing_sigma_seconds <= 0.0):
        raise ValueError("motion periods, duration, and smoothing sigma must be positive")
    if any(not math.isclose(duration / period, round(duration / period)) for period in periods):
        raise ValueError("period must divide loop duration")
    count = round(duration / step)
    times = [index * step for index in range(count)]
    primary = profile.heave_pitch_period_seconds
    harmonic = profile.harmonic_period_seconds
    heave_raw = [
        math.sin(2 * math.pi * time / primary)
        + profile.heave_harmonic_weight * math.sin(2 * math.pi * time / harmonic + 0.35)
        for time in times
    ]
    pitch_raw = [
        math.sin(2 * math.pi * time / primary + math.radians(profile.pitch_phase_degrees))
        + profile.pitch_harmonic_weight * math.sin(2 * math.pi * time / harmonic + 1.10)
        for time in times
    ]
    pitch_raw = _cyclic_gaussian(pitch_raw, profile.pitch_smoothing_sigma_seconds, step)
    roll_raw = [
        math.sin(2 * math.pi * time / profile.roll_period_seconds + 0.85)
        + 0.10 * math.sin(2 * math.pi * time / harmonic + 2.20)
        for time in times
    ]
    heave = _normalize(heave_raw, profile.heave_units)
    pitch = _normalize(pitch_raw, math.radians(profile.pitch_degrees))
    roll = _normalize(roll_raw, math.radians(profile.roll_degrees))
    samples = [MotionSample(t, h, p, r) for t, h, p, r in zip(times, heave, pitch, roll)]
    first = samples[0]
    samples.append(MotionSample(duration, first.heave, first.pitch_radians,
                                first.roll_radians, first.yaw_radians))
    return samples
