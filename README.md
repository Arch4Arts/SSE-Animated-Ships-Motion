# Animated Ships — Bobbing and Motion

A reproducible NIF transformation tool and mesh-only motion addon for
[Animated Ships](https://www.nexusmods.com/skyrimspecialedition/mods/110260)
on Skyrim Special Edition and Anniversary Edition.

This repository is intended for developers who want to inspect, change, test,
and rebuild every distributed NIF from an original Animated Ships installation
or archive. Generated NIFs are deliberately excluded from Git.

## What the addon changes

The generator patches exactly 40 travelling-ship meshes:

- 22 files directly under `Distant/`
- 18 files directly under `NarrowPath/`

It does not patch `UpDown`, LOD, `DISTANT_BASE.nif`, `NARROWPATH_BASE.nif`,
plugins, scripts, routes, or placed references. Mesh classification is based on
the filename: names containing `rowboat` use the Rowboat profile, names
containing `longboat` use the Longboat profile, and all other supported route
meshes use the Large Ship profile.

Each generated NIF receives two related transformations:

1. `SHIPBODY` gets local Heave, Pitch, and Roll keys representing water
   response. No local Yaw is added to `SHIPBODY`.
2. The original route translation coordinates are preserved, but their times
   are remapped by hull mass and upcoming turn demand. Original sparse course
   rotation is replaced by dense, linearly interpolated, Gaussian-filtered
   inertial heading keys.

The output remains a mesh-only addon: no ESP/ESL, Papyrus, SKSE DLL, MCM,
Nemesis, Pandora, or FNIS output is required.

## Current motion profiles

All amplitudes are peak absolute values after normalization. Positive and
negative oscillation therefore span twice the listed amplitude from extreme to
extreme. Heave and sink values are Skyrim/NIF units; angular values are degrees.

### Distant amplitudes

| Hull class | Heave | Pitch | Roll | Sink offset |
| --- | ---: | ---: | ---: | ---: |
| Rowboat | 6.0 | 1.53333335° | 7.0° | -19.0 |
| Longboat | 15.0 | 1.62° | 4.6666667° | -24.5 |
| Large Ship | 21.3333333 | 1.3° | 4.5° | 0.0 |

### NarrowPath amplitudes

| Hull class | Heave | Pitch | Roll | Sink offset |
| --- | ---: | ---: | ---: | ---: |
| Rowboat | 4.5 | 1.1° | 5.2° | -19.0 |
| Longboat | 11.25 | 1.17° | 3.3333333° | -24.5 |
| Large Ship | 14.6666667 | 0.95° | 3.3° | 0.0 |

`wreck` and `sinking` filenames retain the timing and sink offset of their hull
class, but their Heave/Pitch/Roll amplitudes are multiplied by `0.85` in
`Distant` and `0.75` in `NarrowPath`.

### Wave response and loop timing

| Hull class | Heave/Pitch period | Harmonic period | Roll period | Full loop | Pitch lead | Pitch Gaussian sigma | Heave harmonic | Pitch harmonic | Keys at 0.25 s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Rowboat | 3.0 s | 1.5 s | 4.0 s | 12.0 s | 45° | 0.20 s | 0.16 | 0.14 | 49 |
| Longboat | 7.5 s | 3.75 s | 12.0 s | 60.0 s | 55° | 0.75 s | 0.13 | 0.11 | 241 |
| Large Ship | 16.0 s | 8.0 s | 32.0 s | 96.0 s | 65° | 2.50 s | 0.08 | 0.06 | 385 |

For every 0.25-second sample, the generator evaluates:

```text
Heave = sin(primary wave)
      + heave_harmonic_weight * sin(harmonic wave + 0.35 rad)

Pitch = GaussianFilter(
          sin(primary wave + pitch_phase_degrees)
        + pitch_harmonic_weight * sin(harmonic wave + 1.10 rad)
        )

Roll  = sin(roll wave + 0.85 rad)
      + 0.10 * sin(harmonic wave + 2.20 rad)
```

Each component is normalized to its configured amplitude. Pitch uses a cyclic
Gaussian filter, so smoothing also remains continuous across the loop seam.
The first sample is repeated at the full-loop time; every configured component
period must divide the loop duration exactly.

### Route speed and inertial heading

| Hull class | Route time multiplier | Lookahead | Minimum turn-speed factor | Heading Gaussian sigma | Effective cruise speed | Effective maximum-turn speed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Rowboat | 1.00 | 3 segments | 0.75 | 2.0 s | 100% | 75% |
| Longboat | 1.25 | 6 segments | 0.65 | 6.0 s | 80% | 52% |
| Large Ship | 2.00 | 10 segments | 0.55 | 15.0 s | 50% | 27.5% |

The route algorithm keeps every original translation coordinate. For each
segment it accumulates signed heading changes ahead of the ship and a reduced
history term (`0.6 ×` the accumulated turn behind it). The larger absolute
demand is normalized against 90 degrees and passed through Smoothstep:

```text
x = clamp(abs(turn_demand) / 90°, 0, 1)
turn_strength = x² * (3 - 2x)
speed_factor = 1 - (1 - minimum_turn_speed) * turn_strength
new_segment_time = original_segment_time * route_time_multiplier / speed_factor
```

Course headings are unwrapped across ±π, sampled every approximately 0.5
seconds, and cyclically filtered with the class-specific Gaussian sigma before
being written as linear Z-rotation keys. This is the inertial course rotation;
it is separate from local `SHIPBODY` Heave/Pitch/Roll.

`turn_smoothing_radius` values `1/2/3` remain serialized in the profile and
manifest for Rowboat/Longboat/Large Ship, but the current v8 route-time mapper
does not consume that legacy field. Turn response is controlled by lookahead,
minimum speed, and heading sigma as described above.

## Developer requirements

The supported reproducible build environment is Windows with:

- Git
- Python 3.12 or newer
- [PyNifly](https://github.com/BadDogSkyrim/PyNifly), specifically a checkout
  or release containing `io_scene_nifly/pyn`
- 7-Zip when the source is an archive or when creating the distributable `.7z`
- A legally obtained original Animated Ships archive or unpacked installation

Skyrim, Mod Organizer 2, Creation Kit, xEdit, Blender, SKSE, and a Nexus API key
are not required to run the generator. Skyrim and a mod manager are only needed
for in-game testing.

The project has no third-party Python package declared in `pyproject.toml`.
PyNifly is loaded directly from the path supplied to the command.

## Clone and configure

```powershell
git clone https://github.com/Arch4Arts/SSE-Animated-Ships-Motion.git
Set-Location SSE-Animated-Ships-Motion

$env:PYNIFLY_ROOT='M:\Tools\PyNifly\io_scene_nifly'
$env:ANIMATED_SHIPS_MESH_ROOT='M:\Games\MO2\mods\Animated Ships\Meshes\Clutter\Vicn\AnimatedShip'
```

`PYNIFLY_ROOT` must contain the `pyn` directory. The mesh-root variable is used
by the complete integration test suite. The public release builder can instead
discover this directory inside an unpacked mod or archive.

## Run the tests

Pure motion and route tests do not read real NIFs:

```powershell
python -m unittest tests.test_curves tests.test_route_timing -v
```

The complete suite requires both environment variables and performs real NIF
patching, complete 40-mesh builds, validation, archive extraction, and release
packaging:

```powershell
python -m unittest discover -s tests -v
```

Expected current result on Windows with 7-Zip available:

```text
Ran 40 tests
OK
```

## Rebuild from the original archive

No manual extraction is required:

```powershell
python scripts/build_release.py `
  --input 'D:\Downloads\Animated Ships-110260-1-2-0-1709576413.7z' `
  --output 'M:\Build\Animated Ships - Bobbing and Motion 1.0.0' `
  --pynifly $env:PYNIFLY_ROOT `
  --archive 'M:\Build\Animated Ships - Bobbing and Motion-1.0.0.7z'
```

For an unpacked source, pass the mod directory to `--input`:

```powershell
python scripts/build_release.py `
  --input 'M:\Games\MO2\mods\Animated Ships' `
  --output 'M:\Build\Animated Ships - Bobbing and Motion' `
  --pynifly $env:PYNIFLY_ROOT
```

Use `--seven-zip 'X:\Path\To\7z.exe'` when 7-Zip is not installed at
`C:\Program Files\7-Zip\7z.exe`.

The command intentionally refuses to overwrite an existing output directory or
archive. Archive extraction happens in a temporary directory beside the output,
not on the system drive when the output is located elsewhere.

Successful output:

```text
built=40 Distant=22 NarrowPath=18 failed=0 valid=True meshes=40 archive=<path>
```

The working output contains `manifest.json` plus the `Meshes` tree. The optional
distributable `.7z` contains only:

```text
Meshes/
└── Clutter/
    └── Vicn/
        └── AnimatedShip/
            ├── Distant/       # 22 NIFs
            └── NarrowPath/    # 18 NIFs
```

There is no wrapper folder in the archive, so it can be installed directly by
MO2 or another mod manager.

## Lower-level development commands

When iterating on already extracted source meshes, build and validate separately:

```powershell
python scripts/build_patch.py `
  --source $env:ANIMATED_SHIPS_MESH_ROOT `
  --output 'M:\Build\animated-ships-motion' `
  --pynifly $env:PYNIFLY_ROOT

python scripts/validate_patch.py `
  --source $env:ANIMATED_SHIPS_MESH_ROOT `
  --output 'M:\Build\animated-ships-motion' `
  --pynifly $env:PYNIFLY_ROOT `
  --report 'M:\Build\validation-report.json'
```

Validation checks include:

- exactly 40 generated NIFs and 40 manifest entries
- original route translation values and mesh structure remain unchanged
- route translation times match the computed class/turn time map
- dense inertial heading keys match the expected Gaussian-filtered headings
- Heave/Pitch/Roll key counts and profile data match the source code
- source and output SHA-256 hashes match the manifest
- collision attachment maps remain unchanged
- no ESP, ESL, ESM, scripts, or DLLs appear in output

## Editing the motion model

The main implementation files are:

- `src/ship_motion/profiles.py` — every hull coefficient and filename classifier
- `src/ship_motion/curves.py` — local Heave/Pitch/Roll curve generation
- `src/ship_motion/route_timing.py` — turn demand, speed mapping, heading inertia
- `src/ship_motion/nif_patch.py` — PyNifly read/write and preservation checks
- `src/ship_motion/batch.py` — 40-mesh discovery, manifest, batch validation
- `src/ship_motion/release.py` — archive/folder input and release packaging

Recommended change cycle:

1. Change or add a test describing the intended coefficient or algorithm.
2. Run that focused test and confirm it fails for the intended reason.
3. Edit the relevant implementation file.
4. Run the focused test again.
5. Run the complete 40-test suite against original NIFs.
6. Build into a new output path and inspect the generated manifest.
7. Test the resulting meshes in game before publishing them.

Do not use generated ParallaxGen, DynDOLOD, Synthesis, or other tool-output
meshes as build sources. Always regenerate from the original Animated Ships
route meshes, then rerun downstream mesh-generation tools for in-game use.

## Installing the generated addon

Install the generated `.7z` after Animated Ships. If ParallaxGen or another
generated output normally wins these files, rebuild that output after installing
the addon so it inherits the new animation data.

Because the addon contains only replacement NIFs, it can be installed or
removed during an existing playthrough after exiting the game. It stores no
data in saves.

## AI disclosure

This project was developed with substantial assistance from OpenAI Codex. The
human author directed the visual goals, coefficient tuning, in-game evaluation,
and release decisions. AI assisted with NIF analysis, generator code, tests,
validation, and developer documentation.

## License

Source code and repository documentation are available under the
[MIT License](LICENSE). Original Animated Ships assets and generated derivative
NIFs are not covered by this repository license and are not stored in Git.
