# Build and Validation

## Dependencies

- Python 3.12 or newer
- PyNifly checkout/release containing `io_scene_nifly`
- An installed copy of Animated Ships containing its original route meshes

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

The v7 baseline expects 29 passing tests.

## Build

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
