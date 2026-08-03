# Animated Ships — Bobbing and Motion

## Overview

Animated Ships — Bobbing and Motion makes travelling vessels feel present on
the water instead of sliding across it as rigid scenery. It adds class-specific
Heave, Pitch, and Roll, retunes movement speed by hull size, and smooths course
changes with inertial rotation.

## Features

- Fast, readable water response for rowboats
- Responsive but weightier longboat motion
- Slow, imposing movement for large ships
- Smooth course rotation through sharp route corners
- Moderate slowdown based on upcoming turn severity
- Separate lower-amplitude profiles for constrained NarrowPath meshes
- No plugin, Papyrus script, SKSE DLL, or runtime polling

## Requirements

- Skyrim Special Edition or Anniversary Edition
- Animated Ships

## Installation

Install the archive with Mod Organizer 2 and place it after Animated Ships. The
archive contains only replacement meshes and a build manifest.

If you use ParallaxGen, run it again after installing or updating this mod.
Otherwise its older generated mesh can continue to override the new animation.

## Compatibility

Any mod replacing the same Animated Ships NIFs will conflict at the file level;
the last winning mesh supplies the animation. This project does not modify ESP
records, scripts, quests, routes, or placed references.

## Troubleshooting

If ships still snap during turns, check which mod wins the affected mesh. A
stale generated-output mod is the most likely cause. If a ship clips nearby
geometry, confirm that the intended `NarrowPath` variant wins.

## Credits

- Animated Ships and its authors for the underlying ship system and assets
- PyNifly/Nifly contributors for NIF tooling
- Bethesda Game Studios for Skyrim
