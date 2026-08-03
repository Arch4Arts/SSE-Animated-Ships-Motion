from dataclasses import dataclass


@dataclass(frozen=True)
class MotionProfile:
    heave_units: float
    pitch_degrees: float
    roll_degrees: float
    heave_pitch_period_seconds: float
    harmonic_period_seconds: float
    roll_period_seconds: float
    loop_duration_seconds: float
    route_time_multiplier: float
    turn_smoothing_radius: int
    sink_offset_units: float
    yaw_sigma_seconds: float
    turn_lookahead_segments: int
    minimum_turn_speed: float


_DISTANT_PROFILES = {
    "rowboat": MotionProfile(6.0, 1.53333335, 7.0, 4.0, 2.0, 4.0, 8.0, 1.0, 1, -19.0, 2.0, 3, 0.75),
    "longboat": MotionProfile(15.0, 1.62, 4.6666667, 10.0, 5.0, 15.0, 30.0, 1.25, 2, -24.5, 6.0, 6, 0.65),
    "large": MotionProfile(21.3333333, 1.3, 4.5, 10.0, 5.0, 30.0, 30.0, 2.0, 3, 0.0, 15.0, 10, 0.55),
}

_NARROW_PROFILES = {
    "rowboat": MotionProfile(4.5, 1.1, 5.2, 4.0, 2.0, 4.0, 8.0, 1.0, 1, -19.0, 2.0, 3, 0.75),
    "longboat": MotionProfile(11.25, 1.17, 3.3333333, 10.0, 5.0, 15.0, 30.0, 1.25, 2, -24.5, 6.0, 6, 0.65),
    "large": MotionProfile(14.6666667, 0.95, 3.3, 10.0, 5.0, 30.0, 30.0, 2.0, 3, 0.0, 15.0, 10, 0.55),
}


def hull_class(filename: str) -> str:
    lowered = filename.casefold()
    if "rowboat" in lowered:
        return "rowboat"
    if "longboat" in lowered:
        return "longboat"
    return "large"


def _scaled(profile: MotionProfile, factor: float) -> MotionProfile:
    return MotionProfile(
        profile.heave_units * factor,
        profile.pitch_degrees * factor,
        profile.roll_degrees * factor,
        profile.heave_pitch_period_seconds,
        profile.harmonic_period_seconds,
        profile.roll_period_seconds,
        profile.loop_duration_seconds,
        profile.route_time_multiplier,
        profile.turn_smoothing_radius,
        profile.sink_offset_units,
        profile.yaw_sigma_seconds,
        profile.turn_lookahead_segments,
        profile.minimum_turn_speed,
    )


def classify_mesh(folder: str, filename: str) -> MotionProfile:
    if folder not in {"Distant", "NarrowPath"}:
        raise ValueError(f"unsupported route folder: {folder}")
    kind = hull_class(filename)
    lowered = filename.casefold()
    if "wreck" in lowered or "sinking" in lowered:
        return _scaled(_DISTANT_PROFILES[kind], 0.85 if folder == "Distant" else 0.75)
    return (_DISTANT_PROFILES if folder == "Distant" else _NARROW_PROFILES)[kind]
