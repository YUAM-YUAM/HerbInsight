"""Run the repository's dependency-light function tests from any working directory."""
from pathlib import Path
import os
import runpy
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
os.chdir(root)
count = 0
for path in sorted((root / "tests").glob("test_*.py")):
    for name, function in runpy.run_path(str(path)).items():
        if name.startswith("test_") and callable(function):
            function()
            count += 1
            print("PASS", path.name, name, flush=True)
print("TOTAL_PASS", count, flush=True)
