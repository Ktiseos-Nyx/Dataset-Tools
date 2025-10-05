#!/usr/bin/env python3
"""Quick script to help fix f-string logging violations.
Run this to get a list of files and violations that need manual fixing.
"""

import subprocess
from pathlib import Path


def get_fstring_violations():
    """Get all f-string logging violations from ruff."""
    result = subprocess.run([
        "ruff", "check", "dataset_tools/", "--select=G004", "--output-format=json"
    ], check=False, capture_output=True, text=True)

    if result.returncode != 0:
        import json
        violations = json.loads(result.stdout)

        # Group by file
        files_by_violation_count = {}
        for violation in violations:
            filename = violation["filename"]
            if filename not in files_by_violation_count:
                files_by_violation_count[filename] = []
            files_by_violation_count[filename].append({
                "line": violation["location"]["row"],
                "column": violation["location"]["column"],
                "message": violation["message"]
            })

        return files_by_violation_count
    return {}

def print_violation_summary():
    """Print a summary of violations by file for easy fixing."""
    violations = get_fstring_violations()

    if not violations:
        print("✅ No f-string logging violations found!")
        return

    print(f"Found f-string logging violations in {len(violations)} files:")
    print("=" * 60)

    # Sort by number of violations (most first)
    sorted_files = sorted(violations.items(), key=lambda x: len(x[1]), reverse=True)

    for filename, file_violations in sorted_files:
        relative_path = str(Path(filename).relative_to(Path.cwd()))
        print(f"\n📁 {relative_path} ({len(file_violations)} violations)")
        print("-" * 40)

        for v in file_violations[:5]:  # Show first 5 violations per file
            print(f"  Line {v['line']:3d}: {v['message']}")

        if len(file_violations) > 5:
            print(f"  ... and {len(file_violations) - 5} more violations")

    print("\n" + "=" * 60)
    print(f"Total violations: {sum(len(v) for v in violations.values())}")
    print("\nTo fix these:")
    print('1. Replace f"string {var}" with "string %s", var')
    print('2. Replace f"string {var:.2f}" with "string %.2f", var')
    print('3. For multiple variables: f"a {x} b {y}" → "a %s b %s", x, y')

if __name__ == "__main__":
    print_violation_summary()
