# v7: Inertial Course Rotation

## Goal

Make ships rotate continuously through polyline route turns without changing
route coordinates or stopping. Preserve class cruise multipliers, apply
moderate angle-dependent slowdown, and increase rotational inertia with hull
size.

## Profiles

| Hull | Gaussian sigma | Lookahead | Minimum turn speed |
|---|---:|---:|---:|
| Rowboat | 2 s | 3 segments | 75% |
| Longboat | 6 s | 6 segments | 65% |
| Large Ship | 15 s | 10 segments | 55% |

For every route interval, v7 accumulates signed turns over the lookahead window,
keeps a shorter recovery tail, maps the effective angle through smoothstep, and
divides interval duration by the resulting speed factor. Straight speed is
unchanged and speed never reaches zero.

Source Z headings are unwrapped, mapped onto the retimed route, sampled every
0.5 seconds, and passed through a cyclic Gaussian filter. The output uses dense
linear Z keys. The filter wraps with total route winding so both course and
angular velocity remain continuous across the animation seam.

## Safety Boundary

- Translation values and counts remain exactly equal to the source.
- No duplicate or stationary translation key is introduced.
- Source headings retain their authored orientation offset.
- Local bobbing Yaw remains zero.
- Node, shape, collision, plugin, and script structure remains unchanged.
- Generated ParallaxGen output is never an authoring source.

The Imperial Ship regression fixture limits adjacent course change to below 10
degrees; the rejected predecessor produced a measured jump near 56.9 degrees.
