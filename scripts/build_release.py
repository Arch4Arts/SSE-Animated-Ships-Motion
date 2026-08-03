import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from ship_motion.release import build_release


DEFAULT_SEVEN_ZIP = Path(r"C:\Program Files\7-Zip\7z.exe")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a validated MO2-ready Animated Ships motion override"
    )
    parser.add_argument("--input", required=True, type=Path, help="Unpacked Animated Ships folder or source archive")
    parser.add_argument("--output", required=True, type=Path, help="New output folder")
    parser.add_argument("--pynifly", required=True, type=Path, help="Folder containing the pyn package")
    parser.add_argument("--archive", type=Path, help="Optional new MO2-ready .7z path")
    parser.add_argument("--seven-zip", type=Path, default=DEFAULT_SEVEN_ZIP, help="Path to 7z.exe")
    args = parser.parse_args()
    summary = build_release(args.input, args.output, args.pynifly, args.seven_zip, args.archive)
    print(" ".join(f"{key}={value}" for key, value in summary.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
