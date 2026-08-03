# Riften longboat route collision

## Status

Open investigation. This records the observed problem without applying a fix.

## Symptom

Two longboats in Riften can visually intersect while travelling their routes.
The area also appears unusually busy because Animated Ships defines several
independent ship references there.

## Confirmed records

| Runtime FormID | Plugin FormID | EditorID | Base activator |
| --- | --- | --- | --- |
| `FE0128C1` | `0008C1:AnimatedShips.esl` | `zxSHRiftenShipRef03` | `zxActNarrowShipLong01BlackBriar_NRA` (`00095B`) |
| `FE0128FC` | `0008FC:AnimatedShips.esl` | `zxSHRiftenShipRef04` | `zxActNarrowShipLong01Courier01_NRA` (`00084E`) |

Both references are defined by `AnimatedShips.esl`, use scale `0.9`, and resolve
to the same route mesh:

`Meshes\Clutter\Vicn\AnimatedShip\NarrowPath\shiplongboat01Courier01.nif`

Their anchors are close together and their initial rotations face in nearly
opposite directions. The Black-Briar activator has `RandomAnimStart`; the
Courier activator does not.

## Riften traffic count

`AnimatedShips.esl` defines six references whose EditorID matches
`RiftenShipRef`: four primary longboats, one smaller angler longboat, and one
night route. The motion addon does not add ship references.

## Current hypotheses

The root cause has not yet been isolated. Candidate contributors are:

1. Original opposing routes have insufficient lateral separation.
2. Retimed route movement changes when the ships meet.
3. Inertial yaw increases the swept area of the bow and stern.
4. `RandomAnimStart` produces a load-dependent phase for only one ship.

## Evidence needed

- A short video covering several seconds before and after the intersection.
- Whether the contact happens on a straight segment or during a turn.
- Whether it reproduces after leaving and re-entering Riften or loading a save.
- A comparison with the motion addon disabled using the same save and viewpoint.

## Minimal debugging sequence

1. Reproduce with the current release candidate.
2. Repeat with the original `shiplongboat01Courier01.nif` while leaving the
   plugin load order unchanged.
3. If the original does not intersect, compare translation timing first, then
   yaw, changing only one variable per test.
4. If the original also intersects, investigate a Riften-specific record or
   route-spacing patch instead of changing the universal longboat mesh.

