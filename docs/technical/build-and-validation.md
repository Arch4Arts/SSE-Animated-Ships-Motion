# Build and Validation

## Dependencies

- Python 3.12 or newer
- PyNifly checkout/release containing `io_scene_nifly`
- A legally obtained archive or unpacked copy of Animated Ships
- 7-Zip when reading an archive or creating a release archive

```powershell
$env:ANIMATED_SHIPS_MESH_ROOT='X:\Path\To\Animated Ships\Meshes\Clutter\Vicn\AnimatedShip'
$env:PYNIFLY_ROOT='X:\Path\To\io_scene_nifly'
```

## Test

Pure curve and timing tests need no external assets:

```powershell
python -m unittest tests.test_curves tests.test_route_timing -v
```

The complete suite patches representative real NIFs and builds all 40 meshes:

```powershell
python -m unittest discover -s tests -v
```

The complete v8 suite expects 40 passing tests on Windows with 7-Zip available.

## One-command release build

The recommended command accepts the original downloaded archive without manual
extraction:

```powershell
python scripts/build_release.py `
  --input "D:\skyrimMods\Animated Ships-110260-1-2-0-1709576413.7z" `
  --output "M:\Build\Animated Ships - Bobbing and Motion" `
  --pynifly $env:PYNIFLY_ROOT `
  --archive "M:\Build\Animated Ships - Bobbing and Motion-1.0.0.7z"
```

To use an unpacked mod, replace `--input` with the directory containing it. The
builder recursively locates the unique `AnimatedShip` directory with 22
`Distant` and 18 `NarrowPath` route meshes.

The output directory contains the MO2 `Meshes` tree and `manifest.json` for
reproducibility. The optional `.7z` contains only `Meshes` at archive root:

```text
Animated Ships - Bobbing and Motion-1.0.0.7z
└── Meshes
    └── Clutter
        └── Vicn
            └── AnimatedShip
                ├── Distant       (22 NIFs)
                └── NarrowPath    (18 NIFs)
```

The command refuses to overwrite either output. Archive extraction uses a
temporary directory beside `--output`, so a system drive is not consumed when
the output is placed elsewhere. Pass `--seven-zip` if `7z.exe` is not installed
at `C:\Program Files\7-Zip\7z.exe`.

## Build

The following lower-level command requires the exact unpacked mesh root and is
intended for development:

```powershell
python scripts/build_patch.py `
  --source $env:ANIMATED_SHIPS_MESH_ROOT `
  --output build/Animated-Ships-Bobbing-and-Motion `
  --pynifly $env:PYNIFLY_ROOT
```

The expected summary is `built=40 Distant=22 NarrowPath=18 failed=0`.

## Validate

```powershell
python scripts/validate_patch.py `
  --source $env:ANIMATED_SHIPS_MESH_ROOT `
  --output build/Animated-Ships-Bobbing-and-Motion `
  --pynifly $env:PYNIFLY_ROOT
```

The expected result is `valid=true meshes=40 route_mismatches=0
source_hash_mismatches=0 forbidden_files=0`.
