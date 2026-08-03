# Animated Ships — Bobbing and Motion

A motion patch and reproducible NIF generator for
[Animated Ships](https://www.nexusmods.com/skyrimspecialedition/mods/110260)
on Skyrim Special Edition.

The project adds visible hull response while ships travel: vertical **Heave**,
bow **Pitch**, lateral **Roll**, mass-dependent route speed, and dense inertial
course rotation. Rowboats react quickly, longboats remain responsive, and large
ships turn and rock with substantially more inertia.

## v8 hull response

| Hull | Heave/Pitch cycle | Roll cycle | Pitch lead | Pitch smoothing |
|---|---:|---:|---:|---:|
| Rowboat | 3 s | 4 s | 45° | 0.20 s |
| Longboat | 7.5 s | 12 s | 55° | 0.75 s |
| Large Ship | 16 s | 32 s | 65° | 2.50 s |

Heave and Pitch respond to the same notional wave instead of moving as
unrelated oscillators. Secondary surface detail decreases with hull mass.
`Distant` and `NarrowPath` use the same timing for a hull class but retain
different amplitudes for route clearance.

## Requirements

- Skyrim Special Edition or Anniversary Edition
- Animated Ships
- Mod Organizer 2 is recommended
- ParallaxGen users must regenerate its output after installing or updating
  this patch

PyNifly and the original Animated Ships meshes are required only for developers
who want to reproduce a build. They are not included in this repository.

## Installation

Download a ready-to-install archive from GitHub Releases (or the future Nexus
page), install it as a normal MO2 mod, and place it after Animated Ships. If
`PGPatcher_Output` wins the same meshes, rerun ParallaxGen so its generated copy
inherits the new animation data.

Generated NIFs are distributed as release artifacts; they are deliberately not
stored in Git history.

## Reproduce a release

The public builder accepts either the original Animated Ships archive or an
unpacked mod folder. It discovers the internal mesh path automatically, builds
all 40 route meshes, validates them, and can create a ready-to-install `.7z`.

Required build tools:

- Python 3.12 or newer
- PyNifly containing the `io_scene_nifly/pyn` package
- 7-Zip for archive input or release packaging
- A legally obtained copy of Animated Ships

Skyrim, MO2, and Creation Kit are not required to run the builder.

Build directly from the downloaded original archive:

```powershell
python scripts/build_release.py `
  --input "D:\Downloads\Animated Ships-110260-1-2-0-1709576413.7z" `
  --output "M:\Build\Animated Ships - Bobbing and Motion" `
  --pynifly "M:\Tools\PyNifly\io_scene_nifly" `
  --archive "M:\Build\Animated Ships - Bobbing and Motion-1.0.0.7z"
```

For an unpacked source, pass its mod folder to `--input` instead. Both the
output folder and optional archive must not already exist. The distributable
archive opens directly to `Meshes/`; it has no extra wrapper folder and can be
installed normally in MO2.

## Development

Set the two source paths and run the tests from the repository root:

```powershell
$env:ANIMATED_SHIPS_MESH_ROOT='M:\SkyrimModding\MO2\mods\Animated Ships\Meshes\Clutter\Vicn\AnimatedShip'
$env:PYNIFLY_ROOT='M:\SkyrimModding\ForLLMStorage\animated-ships-bobbing-analysis\PyNiflyRelease\io_scene_nifly'
python -m unittest discover -s tests -v
```

The lower-level build and validation commands remain available for development:

```powershell
python scripts/build_patch.py --source $env:ANIMATED_SHIPS_MESH_ROOT --output build/animated-ships-motion --pynifly $env:PYNIFLY_ROOT
python scripts/validate_patch.py --source $env:ANIMATED_SHIPS_MESH_ROOT --output build/animated-ships-motion --pynifly $env:PYNIFLY_ROOT
```

Technical details and design history live in [`docs/`](docs/).

## License

The source code and documentation are available under the [MIT License](LICENSE).
