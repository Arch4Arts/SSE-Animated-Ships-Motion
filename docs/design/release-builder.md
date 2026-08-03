# Release Builder Design

## Goal

Provide one public command that accepts either an unpacked Animated Ships mod
or its original archive and produces a validated MO2-ready mesh override.

## Interface

```powershell
python scripts/build_release.py --input <folder-or-archive> --output <folder> --pynifly <folder> [--archive <file.7z>] [--seven-zip <7z.exe>]
```

The output directory contains `Meshes/Clutter/Vicn/AnimatedShip`, 40 patched
route NIFs, and a build manifest. When `--archive` is supplied, the distributable
contains only the `Meshes` tree at archive root.

## Source discovery

Folder input is searched recursively for the unique directory containing
`Distant` and `NarrowPath` with the expected 22/18 route meshes. Archive input
is extracted to an automatically cleaned temporary directory through 7-Zip and
then follows the same discovery path. Ambiguous and incomplete inputs fail with
an actionable error.

## Safety and validation

- Existing output and archive paths are never overwritten.
- The existing v8 builder remains the only NIF transformation implementation.
- The complete validator must report 40 meshes and no mismatches before an
  optional release archive is created.
- Skyrim, MO2, and Creation Kit are not build dependencies.

