from dataclasses import dataclass
import hashlib
from pathlib import Path
import sys

from .curves import sample_motion
from .profiles import MotionProfile
from .route_timing import build_time_map, sample_inertial_headings


@dataclass(frozen=True)
class PatchResult:
    source_sha256: str
    output_sha256: str
    base_z: float
    key_count: int
    yaw_key_count: int
    route_signature_sha256: str
    mapped_route_duration: float
    original_route_duration: float
    max_curvature_degrees: float
    max_turn_strength: float
    route_rotation_key_count: int
    max_rotation_step_degrees: float
    max_rotation_rate: float
    minimum_speed_factor: float


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _key_value(key):
    value = key.value
    try:
        return [float(component) for component in value]
    except TypeError:
        return float(value)


def _route_sequence(nif):
    manager = nif.root.controller
    sequence = manager.sequences.get("SpecialIdle")
    if sequence is None or len(sequence.controlled_blocks) != 1:
        raise ValueError("expected one SpecialIdle route block")
    return manager, sequence, sequence.controlled_blocks[0]


def route_value_signature(nif: object) -> dict[str, object]:
    _, sequence, link = _route_sequence(nif)
    data = link.interpolator.data
    return {
        "node_name": link.node_name,
        "controller_type": link.controller_type,
        "property_type": link.property_type,
        "priority": int(link.properties.priority),
        "translation_interpolation": int(data.properties.translations.interpolation),
        "z_interpolation": int(data.properties.zRotations.interpolation),
        "translations": [_key_value(key) for key in data.translations],
        "zrotations": [
            (_key_value(key), float(getattr(key, "forward", 0.0)),
             float(getattr(key, "backward", 0.0))) for key in data.zrotations
        ],
        "cycle_type": int(sequence.properties.cycleType),
        "frequency": float(sequence.properties.frequency),
        "weight": float(sequence.properties.weight),
        "text_values": [value for _, value in sequence.text_key_data.keys],
    }


def route_timing_signature(nif: object) -> dict[str, object]:
    _, sequence, link = _route_sequence(nif)
    data = link.interpolator.data
    return {
        "start": float(sequence.properties.startTime),
        "stop": float(sequence.properties.stopTime),
        "translations": [float(key.time) for key in data.translations],
        "zrotations": [float(key.time) for key in data.zrotations],
        "text": [(float(time), value) for time, value in sequence.text_key_data.keys],
    }


def route_signature(nif: object) -> dict[str, object]:
    return {"values": route_value_signature(nif), "timing": route_timing_signature(nif)}


def _retime_route(nif, profile, pyn):
    manager, sequence, link = _route_sequence(nif)
    old_data = link.interpolator.data
    times = [float(key.time) for key in old_data.translations]
    points = [(float(key.value[0]), float(key.value[1])) for key in old_data.translations]
    mapping, stats = build_time_map(
        times, points, profile.route_time_multiplier,
        profile.turn_lookahead_segments, profile.minimum_turn_speed
    )
    if old_data.qrotations or old_data.xrotations or old_data.yrotations or not old_data.zrotations:
        raise ValueError("unsupported route rotation layout")

    NiKeyType = pyn["NiKeyType"]
    new_data = pyn["NiTransformData"].New(
        nif,
        rotation_type=old_data.properties.rotationType,
        xyz_rotation_types=(
            old_data.properties.xRotations.interpolation,
            old_data.properties.yRotations.interpolation,
            NiKeyType.LINEAR_KEY,
        ),
        translate_type=old_data.properties.translations.interpolation,
        scale_type=old_data.properties.scales.interpolation,
    )
    if old_data.properties.translations.interpolation != NiKeyType.LINEAR_KEY:
        raise ValueError("unsupported route translation interpolation")
    for key in old_data.translations:
        buffer = pyn["NiAnimKeyLinearTransBuf"]()
        buffer.time = mapping.map_time(float(key.time))
        buffer.value = pyn["VECTOR3"](*[float(value) for value in key.value])
        pyn["nifly"].addAnimKeyLinearTrans(nif._handle, new_data.id, buffer)
    old_headings = [float(key.value) for key in old_data.zrotations]
    mapped_heading_times = [mapping.map_time(float(key.time)) for key in old_data.zrotations]
    inertial = sample_inertial_headings(
        mapped_heading_times, old_headings, mapping.new_times[-1], profile.yaw_sigma_seconds
    )
    z_keys = []
    for key in inertial:
        buffer = pyn["NiAnimKeyLinearBuf"]()
        buffer.time = key.time
        buffer.value = key.value
        z_keys.append(pyn["LinearScalarKey"](buffer))
    new_data.add_xyz_rotation_keys("Z", z_keys)

    old_interp = link.interpolator
    interp_props = pyn["NiTransformInterpolator"].getbuf()
    interp_props.translation = old_interp.properties.translation
    interp_props.rotation = old_interp.properties.rotation
    interp_props.scale = float(old_interp.properties.scale)
    interp_props.dataID = new_data.id
    new_interp = nif.add_block(None, interp_props)
    new_text = pyn["NiTextKeyExtraData"].New(
        nif, keys=[(mapping.map_time(float(time)), value) for time, value in sequence.text_key_data.keys]
    )
    new_sequence = pyn["NiControllerSequence"].New(
        nif,
        "SpecialIdle",
        accum_root_name=sequence.accumRootName,
        frequency=float(sequence.properties.frequency),
        phase=0.0,
        start_time=mapping.map_time(float(sequence.properties.startTime)),
        stop_time=mapping.map_time(float(sequence.properties.stopTime)),
        cycle_type=sequence.properties.cycleType,
        weight=float(sequence.properties.weight),
        text_key_data=new_text,
        parent=manager,
    )
    new_sequence.add_controlled_block(
        link.node_name,
        interpolator=new_interp,
        controller=link.controller,
        priority=int(link.properties.priority),
        node_name=link.node_name,
        controller_type=link.controller_type,
    )
    return stats, inertial


def patch_nif(source: Path, destination: Path, profile: MotionProfile, pynifly_root: Path) -> PatchResult:
    source, destination = source.resolve(), destination.resolve()
    if source == destination:
        raise ValueError("destination must differ from source")
    if str(pynifly_root) not in sys.path:
        sys.path.insert(0, str(pynifly_root))
    from pyn.nifdefs import NiAnimKeyFloatBuf, NiAnimKeyLinearBuf, NiAnimKeyLinearTransBuf, NiKeyType
    from pyn.pynmathutils import VECTOR3
    from pyn.pynifly import LinearScalarKey, NifFile, NiControllerSequence, NiTextKeyExtraData, NiTransformController, NiTransformData, NiTransformInterpolator, QuadScalarKey, nifly

    pyn = locals()
    source_hash = sha256_file(source)
    nif = NifFile(str(source))
    values_before = route_value_signature(nif)
    stats, inertial = _retime_route(nif, profile, pyn)
    body = nif.nodes["SHIPBODY"]
    controller = body.controller
    base = [float(value) for value in body.transform.translation]
    base[2] += profile.sink_offset_units
    samples = sample_motion(profile)
    data = NiTransformData.New(nif, rotation_type=NiKeyType.XYZ_ROTATION_KEY, xyz_rotation_types=(NiKeyType.LINEAR_KEY,) * 3, translate_type=NiKeyType.LINEAR_KEY)
    x_keys, y_keys = [], []
    for sample in samples:
        for target, value in ((x_keys, sample.pitch_radians), (y_keys, sample.roll_radians)):
            buffer = NiAnimKeyLinearBuf(); buffer.time = sample.time; buffer.value = value; target.append(LinearScalarKey(buffer))
        translation = NiAnimKeyLinearTransBuf(); translation.time = sample.time; translation.value = VECTOR3(base[0], base[1], base[2] + sample.heave); nifly.addAnimKeyLinearTrans(nif._handle, data.id, translation)
    data.add_xyz_rotation_keys("X", x_keys); data.add_xyz_rotation_keys("Y", y_keys)
    interp = NiTransformInterpolator.New(nif, data_block=data)
    NiTransformController.New(nif, flags=8, start_time=0.0, stop_time=profile.loop_duration_seconds, frequency=float(controller.properties.frequency), phase=float(controller.properties.phase), interpolator=interp, target=body, parent=body)
    destination.parent.mkdir(parents=True, exist_ok=True)
    nif.filepath = str(destination); nif.save()
    reopened = NifFile(str(destination))
    values_after = route_value_signature(reopened)
    preserved_keys = (
        "node_name", "controller_type", "property_type", "priority",
        "translation_interpolation", "translations",
        "cycle_type", "frequency", "weight", "text_values",
    )
    if any(values_after[key] != values_before[key] for key in preserved_keys):
        destination.unlink(missing_ok=True); raise ValueError("preserved route values changed")
    count = len(samples)
    reopened_data = reopened.nodes["SHIPBODY"].controller.interpolator.data
    if (len(reopened_data.xrotations), len(reopened_data.yrotations), len(reopened_data.zrotations), len(reopened_data.translations)) != (count, count, 0, count):
        destination.unlink(missing_ok=True); raise ValueError("unexpected SHIPBODY key counts")
    route_steps = [abs(b.value-a.value) for a,b in zip(inertial,inertial[1:])]
    route_rates = [step/(b.time-a.time) for step,a,b in zip(route_steps,inertial,inertial[1:])]
    return PatchResult(
        source_hash, sha256_file(destination), base[2], count, 0,
        hashlib.sha256(repr(values_before).encode()).hexdigest(),
        stats.mapped_duration, stats.original_duration, stats.max_curvature_degrees,
        stats.max_turn_strength, len(inertial),
        max(route_steps, default=0.0)*180.0/3.141592653589793,
        max(route_rates, default=0.0)*180.0/3.141592653589793,
        stats.minimum_speed_factor,
    )
