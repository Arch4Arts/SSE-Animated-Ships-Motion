# Motion Model

## Local hull motion

- **Heave** translates `SHIPBODY` vertically.
- **Pitch** rotates it around the transverse X axis, raising or lowering the bow.
- **Roll** rotates it around the longitudinal Y axis.
- Local **Yaw** is intentionally zero; route course owns Z rotation.

The v8 curve couples Heave and Pitch to one dominant signal, adds a smaller
class-specific harmonic, cyclically filters Pitch, normalizes the results to
their profile amplitudes, and samples at 0.25-second intervals.

| Hull | Dominant | Roll | Pitch lead | Pitch sigma | Harmonic / weights |
|---|---:|---:|---:|---:|---:|
| Rowboat | 3 s | 4 s | 45° | 0.20 s | 1.5 s / 0.16 / 0.14 |
| Longboat | 7.5 s | 12 s | 55° | 0.75 s | 3.75 s / 0.13 / 0.11 |
| Large Ship | 16 s | 32 s | 65° | 2.50 s | 8 s / 0.08 / 0.06 |

The two harmonic weights are Heave and Pitch respectively. Component periods
must divide the configured loop exactly; invalid profiles are rejected instead
of being hidden by an overwritten last key.

## Route motion

The route controller translates the complete vessel through authored XY points.
The generator never adds, removes, duplicates, or moves these points. It only
retimes them and replaces sparse course rotation with dense linear inertial
keys.

`Distant` and `NarrowPath` are asset categories, not runtime readings of open
and sheltered water. They currently select different amplitudes. Weather,
shoreline distance, water type, and live wave simulation are outside scope.

## Generated output

Tools such as ParallaxGen may copy and transform the winning NIF into their own
output mod. That output is downstream and disposable. Always regenerate it
after changing this patch; never copy it back into the source or generator.
