import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from ship_motion.batch import build_patch


def main() -> int:
    parser = argparse.ArgumentParser(description="Build pronounced motion NIFs for Animated Ships")
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--pynifly", required=True, type=Path)
    args = parser.parse_args()
    summary = build_patch(args.source, args.output, args.pynifly)
    print(" ".join(f"{key}={value}" for key, value in summary.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
