# Motion Model

## Local hull motion

- **Heave** translates `SHIPBODY` vertically.
- **Pitch** rotates it around the transverse X axis, raising or lowering the bow.
- **Roll** rotates it around the longitudinal Y axis.
- Local **Yaw** is intentionally zero; route course owns Z rotation.

The v7 curve combines a dominant sine with a smaller harmonic, normalizes the
result to the profile amplitude, and samples at 0.25-second intervals. Hull
profiles control amplitude, period, sink offset, cruise multiplier, turn
lookahead, minimum turn speed, and yaw-filter width.

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
