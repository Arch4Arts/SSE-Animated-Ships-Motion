from collections import Counter
from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
import shutil
import sys
import uuid

from .nif_patch import patch_nif, route_timing_signature, route_value_signature, sha256_file
from .profiles import classify_mesh, hull_class
from .route_timing import build_time_map, sample_inertial_headings

_OUTPUT_MESH_ROOT = Path("Meshes/Clutter/Vicn/AnimatedShip")
_FORBIDDEN = {".esp", ".esl", ".esm", ".pex", ".psc", ".dll"}


@dataclass(frozen=True)
class ValidationReport:
    valid: bool
    meshes: int
    route_mismatches: int
    source_hash_mismatches: int
    forbidden_files: int
    errors: tuple[str, ...]
    def as_dict(self): return asdict(self)


def discover_meshes(source_root: Path) -> list[Path]:
    source_root = source_root.resolve()
    paths = []
    counts = {}
    for folder in ("Distant", "NarrowPath"):
        found = [path for path in (source_root / folder).glob("*.nif") if "base" not in path.name.casefold()]
        counts[folder] = len(found); paths.extend(found)
    if counts != {"Distant": 22, "NarrowPath": 18}:
        raise ValueError(f"unexpected source mesh counts: {counts}")
    return sorted(paths, key=lambda path: str(path.relative_to(source_root)).casefold())


def build_patch(source_root: Path, output_root: Path, pynifly_root: Path) -> dict[str, int]:
    source_root, output_root = source_root.resolve(), output_root.resolve()
    if output_root.exists(): raise FileExistsError(f"output already exists: {output_root}")
    output_root.parent.mkdir(parents=True, exist_ok=True)
    staging = output_root.parent / f"{output_root.name}.staging-{uuid.uuid4().hex}"
    staging.mkdir(); entries = []; counts = {"Distant": 0, "NarrowPath": 0}
    try:
        for source in discover_meshes(source_root):
            relative = source.relative_to(source_root); folder = relative.parts[0]
            profile = classify_mesh(folder, source.name)
            output_relative = _OUTPUT_MESH_ROOT / relative
            result = patch_nif(source, staging / output_relative, profile, pynifly_root)
            counts[folder] += 1
            entries.append({
                "relative_path": relative.as_posix(), "output_path": output_relative.as_posix(),
                "hull_class": hull_class(source.name), "profile": asdict(profile),
                "route_time_multiplier": profile.route_time_multiplier,
                "source_sha256": result.source_sha256, "output_sha256": result.output_sha256,
                "key_count": result.key_count, "yaw_key_count": result.yaw_key_count,
                "original_route_duration": result.original_route_duration,
                "mapped_route_duration": result.mapped_route_duration,
                "max_curvature_degrees": result.max_curvature_degrees,
                "max_turn_strength": result.max_turn_strength,
                "minimum_speed_factor": result.minimum_speed_factor,
                "route_rotation_key_count": result.route_rotation_key_count,
                "max_rotation_step_degrees": result.max_rotation_step_degrees,
                "max_rotation_rate": result.max_rotation_rate,
                "route_value_signature_sha256": result.route_signature_sha256,
            })
        (staging / "manifest.json").write_text(json.dumps({"name":"Animated Ships - Pronounced Sailing Motion","version":7,"variant":"standard","meshes":entries}, indent=2, sort_keys=True), encoding="utf-8")
        staging.rename(output_root)
    except Exception:
        if staging.exists(): shutil.rmtree(staging)
        raise
    return {"built":len(entries), "Distant":counts["Distant"], "NarrowPath":counts["NarrowPath"], "failed":0}


def _load_nif(path, root):
    if str(root) not in sys.path: sys.path.insert(0, str(root))
    from pyn.pynifly import NifFile
    return NifFile(str(path))


def _collision_map(nif):
    return {name:(type(node.collision_object).__name__, type(node.collision_object.body).__name__ if node.collision_object and node.collision_object.body else None) for name,node in nif.nodes.items() if node.collision_object}


def validate_patch(source_root: Path, output_root: Path, pynifly_root: Path) -> ValidationReport:
    source_root, output_root = source_root.resolve(), output_root.resolve()
    errors=[]; route_mismatches=0; source_mismatches=0; forbidden=0
    for path in output_root.rglob("*") if output_root.exists() else []:
        if path.is_file() and path.suffix.casefold() in _FORBIDDEN:
            forbidden += 1; errors.append(f"{path.relative_to(output_root)}: forbidden extension")
    try:
        manifest=json.loads((output_root/"manifest.json").read_text(encoding="utf-8"))
        entries=manifest["meshes"]
        if manifest.get("version") != 7 or manifest.get("variant") != "standard": errors.append("manifest version or variant mismatch")
    except Exception as exc:
        entries=[]; errors.append(f"manifest unreadable: {exc}")
    if len(entries)!=40: errors.append(f"manifest mesh count={len(entries)}, expected=40")
    for entry in entries:
        relative=Path(entry["relative_path"]); label=relative.as_posix(); source=source_root/relative; output=output_root/Path(entry["output_path"])
        try:
            if sha256_file(source)!=entry["source_sha256"]: source_mismatches+=1; errors.append(f"{label}: source hash mismatch")
            if sha256_file(output)!=entry["output_sha256"]: errors.append(f"{label}: output hash mismatch")
            src=_load_nif(source,pynifly_root); out=_load_nif(output,pynifly_root); profile=classify_mesh(relative.parts[0],relative.name)
            src_values=route_value_signature(src); out_values=route_value_signature(out)
            preserved=("node_name","controller_type","property_type","priority","translation_interpolation","translations","cycle_type","frequency","weight","text_values")
            if any(src_values[key]!=out_values[key] for key in preserved): route_mismatches+=1; errors.append(f"{label}: route value mismatch")
            if entry["profile"]!=asdict(profile): errors.append(f"{label}: profile mismatch")
            src_seq=list(src.root.controller.sequences.values())[0]; src_data=src_seq.controlled_blocks[0].interpolator.data
            mapping,stats=build_time_map(
                [float(k.time) for k in src_data.translations],
                [(float(k.value[0]),float(k.value[1])) for k in src_data.translations],
                profile.route_time_multiplier, profile.turn_lookahead_segments,
                profile.minimum_turn_speed)
            timing=route_timing_signature(out)
            expected_times=[mapping.map_time(float(k.time)) for k in src_data.translations]
            if any(not math.isclose(a,b,abs_tol=1e-3) for a,b in zip(timing["translations"],expected_times)): errors.append(f"{label}: route timing mismatch")
            expected_headings=sample_inertial_headings(
                [mapping.map_time(float(k.time)) for k in src_data.zrotations],
                [float(k.value) for k in src_data.zrotations], mapping.new_times[-1],
                profile.yaw_sigma_seconds)
            if len(timing["zrotations"]) != len(expected_headings): errors.append(f"{label}: route rotation count mismatch")
            elif any(not math.isclose(a,b.time,abs_tol=1e-3) for a,b in zip(timing["zrotations"],expected_headings)): errors.append(f"{label}: route rotation timing mismatch")
            if int(out_values["z_interpolation"]) != 1: errors.append(f"{label}: route Z interpolation is not linear")
            data=out.nodes["SHIPBODY"].controller.interpolator.data; expected_count=round(profile.loop_duration_seconds/.25)+1
            if (len(data.xrotations),len(data.yrotations),len(data.zrotations),len(data.translations))!=(expected_count,expected_count,0,expected_count): errors.append(f"{label}: motion key counts mismatch")
            if set(src.nodes)!=set(out.nodes) or Counter(x.name for x in src.shapes)!=Counter(x.name for x in out.shapes): errors.append(f"{label}: structure changed")
            if _collision_map(src)!=_collision_map(out): errors.append(f"{label}: collision attachment map changed")
            if not math.isclose(stats.mapped_duration,entry["mapped_route_duration"],abs_tol=1e-3): errors.append(f"{label}: manifest duration mismatch")
            if not math.isclose(stats.minimum_speed_factor,entry["minimum_speed_factor"],abs_tol=1e-6): errors.append(f"{label}: manifest speed mismatch")
        except Exception as exc: errors.append(f"{label}: validation error: {exc}")
    nif_count=len(list(output_root.rglob("*.nif"))) if output_root.exists() else 0
    if nif_count!=40: errors.append(f"output NIF count={nif_count}, expected=40")
    return ValidationReport(not errors,len(entries),route_mismatches,source_mismatches,forbidden,tuple(errors))
