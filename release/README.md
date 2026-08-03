# Release Packaging

Generated NIFs belong in GitHub Release archives, not Git history.

The ready-to-install archive root must contain:

```text
Meshes/Clutter/Vicn/AnimatedShip/Distant/*.nif
Meshes/Clutter/Vicn/AnimatedShip/NarrowPath/*.nif
manifest.json
```

It must contain exactly 40 generated NIFs: 22 `Distant` and 18 `NarrowPath`.
Do not package source meshes, PyNifly, tests, reports, backups, MO2 metadata,
ParallaxGen output, or temporary staging directories.

Validate the assembled tree with `scripts/validate_patch.py` before creating a
versioned archive. A GitHub Release or Nexus upload is a separate publication
action from committing source code.
