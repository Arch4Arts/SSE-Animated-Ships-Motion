# Changelog

## v8 — Mass-responsive motion

- Coupled Heave and Pitch to one dominant wave response.
- Set dominant periods to 3/7.5/16 seconds for Rowboat/Longboat/Large Ship.
- Set Roll periods to 4/12/32 seconds by hull class.
- Added class-specific Pitch phase lead and cyclic Gaussian inertia.
- Reduced secondary harmonic influence as hull mass increases.
- Replaced forced final-key closure with validated naturally periodic curves.

## v7 — Reproducible baseline

- Added pronounced Heave, Pitch, and Roll without local Yaw.
- Added hull-class route speed profiles and lookahead turn slowdown.
- Replaced sparse quadratic course keys with dense linear inertial rotation.
- Preserved source route coordinates, mesh structure, and collision data.
- Added build and validation coverage for all 40 route meshes.
