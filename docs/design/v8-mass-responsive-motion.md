# v8: Mass-Responsive Hull Motion

## Status

Implemented in source and manifest version 8.

## Goal

Make local hull motion communicate mass while Heave and Pitch remain a coherent
response to one notional wave. Rowboats react quickly, longboats remain
responsive, and large ships build and shed motion slowly.

| Hull | Heave/Pitch cycle | Roll cycle | Loop |
|---|---:|---:|---:|
| Rowboat | 3 s | 4 s | 12 s |
| Longboat | 7.5 s | 12 s | 60 s |
| Large Ship | 16 s | 32 s | 96 s |

Pitch leads the dominant Heave response and receives mass-dependent cyclic
smoothing:

| Hull | Pitch lead | Pitch smoothing sigma |
|---|---:|---:|
| Rowboat | 45 degrees | 0.20 s |
| Longboat | 55 degrees | 0.75 s |
| Large Ship | 65 degrees | 2.50 s |

A small harmonic prevents mechanical repetition. Its period/weight is
`1.5 s / 0.16 / 0.14` for Rowboat, `3.75 s / 0.13 / 0.11` for Longboat, and
`8 s / 0.08 / 0.06` for Large Ship (Heave/Pitch weights respectively).

v8 retains all v7 amplitudes, sink offsets, route coordinates, speed timing,
inertial course rotation, and zero local Yaw. `Distant` and `NarrowPath` remain
route categories: they alter amplitude, not the assumed type of water.

Every component period must divide the configured loop exactly. Position and
first finite-difference velocity must close naturally; the generator must not
hide an invalid loop by overwriting its last sample.
