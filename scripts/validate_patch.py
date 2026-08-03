import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from ship_motion.batch import validate_patch


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate pronounced motion NIFs")
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--pynifly", required=True, type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = validate_patch(args.source, args.output, args.pynifly)
    report_data = report.as_dict()
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report_data, indent=2), encoding="utf-8")
    print(
        f"valid={str(report.valid).lower()} meshes={report.meshes} "
        f"route_mismatches={report.route_mismatches} "
        f"source_hash_mismatches={report.source_hash_mismatches} "
        f"forbidden_files={report.forbidden_files}"
    )
    for error in report.errors:
        print(f"ERROR: {error}")
    return 0 if report.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
