from dataclasses import dataclass
from pathlib import Path


@dataclass
class CheckResult:
    passed: bool
    reason: str


def check_export_succeeded(exported_file_path: str) -> CheckResult:
    """Check 1: did the export actually produce a usable .3mf file?"""
    path = Path(exported_file_path)

    if not path.exists():
        return CheckResult(passed=False, reason=f"File does not exist: {exported_file_path}")

    if path.stat().st_size == 0:
        return CheckResult(passed=False, reason=f"File is empty: {exported_file_path}")

    if path.suffix.lower() != ".3mf":
        return CheckResult(passed=False, reason=f"Expected a .3mf file, got: {path.suffix}")

    return CheckResult(passed=True, reason="Export succeeded: file exists and is a valid .3mf")


def check_geometry_matches(
    original_bounds: dict,
    exported_bounds: dict,
    tolerance_mm: float = 0.1,
) -> CheckResult:
    """
    Check 2: does the exported geometry match the original part's bounding box?

    original_bounds / exported_bounds are dicts like:
        {"x": 10.0, "y": 20.0, "z": 5.0}
    """
    for axis in ("x", "y", "z"):
        if axis not in original_bounds or axis not in exported_bounds:
            return CheckResult(passed=False, reason=f"Missing '{axis}' dimension in bounds")

        diff = abs(original_bounds[axis] - exported_bounds[axis])
        if diff > tolerance_mm:
            return CheckResult(
                passed=False,
                reason=(
                    f"Geometry mismatch on {axis}-axis: original={original_bounds[axis]}mm, "
                    f"exported={exported_bounds[axis]}mm, diff={diff:.3f}mm "
                    f"(tolerance={tolerance_mm}mm)"
                ),
            )

    return CheckResult(passed=True, reason="Geometry matches within tolerance on all axes")


def run_all_checks(
    exported_file_path: str,
    original_bounds: dict,
    exported_bounds: dict,
    tolerance_mm: float = 0.1,
) -> list[CheckResult]:
    """
    Runs the checks in order and stops at the first failure
    (no point checking geometry if the export itself failed).
    """
    results = []

    export_result = check_export_succeeded(exported_file_path)
    results.append(export_result)
    if not export_result.passed:
        return results

    geometry_result = check_geometry_matches(original_bounds, exported_bounds, tolerance_mm)
    results.append(geometry_result)

    return results


if __name__ == "__main__":
    # Manual test 1: file that doesn't exist -> should fail
    result1 = check_export_succeeded("does_not_exist.3mf")
    print(f"Test 1 (missing file): passed={result1.passed}, reason={result1.reason}")

    # Manual test 2: geometry off by 0.3mm on z-axis (tolerance is 0.1mm) -> should fail
    result2 = check_geometry_matches(
        original_bounds={"x": 50.0, "y": 30.0, "z": 20.0},
        exported_bounds={"x": 50.0, "y": 30.0, "z": 20.3},
    )
    print(f"Test 2 (geometry mismatch): passed={result2.passed}, reason={result2.reason}")

    # Manual test 3: run_all_checks with BOTH problems (missing file AND bad geometry).
    # It should stop after the export check, so we expect only 1 result, not 2.
    results3 = run_all_checks(
        exported_file_path="does_not_exist.3mf",
        original_bounds={"x": 50.0, "y": 30.0, "z": 20.0},
        exported_bounds={"x": 50.0, "y": 30.0, "z": 20.3},
    )
    print(f"Test 3 (run_all_checks, both wrong): {len(results3)} result(s) returned")
    for r in results3:
        print(f"  passed={r.passed}, reason={r.reason}")