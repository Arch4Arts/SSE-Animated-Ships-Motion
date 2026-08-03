# Publishing a GitHub Release

## Build the asset

Run `scripts/build_release.py` with `--archive`. Do not upload the working output
folder or GitHub's automatic source archives as the user-facing mod package.

Before publication, extract the generated `.7z` into an empty directory and
confirm that it contains exactly 40 NIFs under the top-level `Meshes` folder.

## Publish

1. Merge the release branch into `main` and rerun the full test suite.
2. Push `main` to GitHub.
3. Open **Releases** and choose **Draft a new release**.
4. Create a tag such as `v1.0.0` targeting `main`.
5. Set the title to `Animated Ships — Bobbing and Motion v1.0.0`.
6. Attach `Animated Ships - Bobbing and Motion-1.0.0.7z`.
7. Save a draft, download and inspect the attached asset, then publish it.

The automatically generated `Source code.zip` and `Source code.tar.gz` contain
the generator source at the tagged commit. They do not contain generated NIFs
and are not substitutes for the attached MO2 archive.
