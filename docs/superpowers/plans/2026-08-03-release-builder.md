# Release Builder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add one command that converts an unpacked folder or original Animated Ships archive into a validated MO2-ready folder and optional `.7z`.

**Architecture:** A focused `ship_motion.release` module resolves or extracts the input, delegates all NIF work to the existing batch builder/validator, and packages only the `Meshes` directory. A thin CLI exposes it without duplicating transformation logic.

**Tech Stack:** Python 3.12 standard library, existing PyNifly integration, 7-Zip CLI, `unittest`.

## Global Constraints

- Support both an unpacked Animated Ships folder and an original archive.
- Require Python 3.12 and PyNifly; require 7-Zip only for archive input/output.
- Produce exactly 40 route NIFs under a top-level `Meshes` directory.
- Never overwrite an existing output directory or archive.
- Do not redistribute original Animated Ships assets in Git history.

---

### Task 1: Input discovery and archive extraction

**Files:**
- Create: `src/ship_motion/release.py`
- Create: `tests/test_release.py`

**Interfaces:**
- Produces: `locate_mesh_root(root: Path) -> Path`
- Produces: `prepared_input(path: Path, seven_zip: Path)` context manager yielding the route mesh root

- [ ] Write tests that locate the unique 22/18 source tree, reject incomplete trees, and extract a real test `.7z` with 7-Zip.
- [ ] Run `python -m unittest tests.test_release -v` and confirm failure because `ship_motion.release` is absent.
- [ ] Implement recursive discovery, archive extraction, cleanup, and explicit errors.
- [ ] Run `python -m unittest tests.test_release -v` and confirm the tests pass.

### Task 2: Validated release output and packaging

**Files:**
- Modify: `src/ship_motion/release.py`
- Modify: `tests/test_release.py`
- Create: `scripts/build_release.py`

**Interfaces:**
- Produces: `build_release(input_path: Path, output_path: Path, pynifly_root: Path, seven_zip: Path, archive_path: Path | None) -> dict`

- [ ] Add failing tests for a 40-NIF output and an archive whose file entries begin at `Meshes/`.
- [ ] Run the focused tests and confirm the expected missing-interface failure.
- [ ] Delegate transformation to `build_patch`, require `validate_patch(...).valid`, and invoke 7-Zip only after validation.
- [ ] Add the argparse CLI and print a concise build/validation/archive summary.
- [ ] Run the focused tests and confirm they pass.

### Task 3: User documentation and integration

**Files:**
- Modify: `README.md`
- Modify: `docs/technical/build-and-validation.md`
- Modify: `CHANGELOG.md`
- Include: `docs/diagnostics/riften-longboat-route-collision.md`

**Interfaces:**
- Consumes: the CLI from Task 2.
- Produces: copyable folder-input and archive-input commands plus dependency and release-layout documentation.

- [ ] Document prerequisites, both input forms, optional packaging, and the exact MO2 archive layout.
- [ ] Run the complete `unittest` suite with real Animated Ships and PyNifly paths.
- [ ] Commit the release builder and diagnostic documentation.
- [ ] Merge `feat/mass-responsive-motion-v8` into `main` and rerun the complete suite on the merged tree.

