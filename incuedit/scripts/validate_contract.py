#!/usr/bin/env python3
"""Check that the hand-maintained OpenAPI contract covers all FastAPI paths/methods."""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import yaml
from app.main import app
contract = yaml.safe_load((ROOT / "openapi.yaml").read_text(encoding="utf-8"))
actual = app.openapi().get("paths", {})
expected = contract.get("paths", {})
missing_paths = sorted(set(actual) - set(expected))
extra_paths = sorted(set(expected) - set(actual))
method_mismatches = []
for path in sorted(set(actual) & set(expected)):
    actual_methods = {k for k in actual[path] if k in {"get", "post", "put", "patch", "delete", "options", "head"}}
    expected_methods = {k for k in expected[path] if k in {"get", "post", "put", "patch", "delete", "options", "head"}}
    if actual_methods != expected_methods:
        method_mismatches.append({"path": path, "fastapi": sorted(actual_methods), "contract": sorted(expected_methods)})
result = {
    "openapi_version": contract.get("openapi"),
    "fastapi_path_count": len(actual),
    "contract_path_count": len(expected),
    "missing_paths": missing_paths,
    "extra_paths": extra_paths,
    "method_mismatches": method_mismatches,
    "passed": not (missing_paths or extra_paths or method_mismatches),
}
print(yaml.safe_dump(result, sort_keys=False))
if not result["passed"]:
    sys.exit(1)
