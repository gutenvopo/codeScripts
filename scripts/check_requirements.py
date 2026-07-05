"""Ensure every imported third-party top-level package is declared."""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "seedrfetch"
REQUIREMENTS = SOURCE_ROOT / "requirements.txt"
IMPORT_TO_PACKAGE = {"PIL": "pillow"}


def imported_modules() -> set[str]:
    modules: set[str] = set()
    for path in SOURCE_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                modules.add(node.module.split(".")[0])
    return modules


def declared_packages() -> set[str]:
    packages: set[str] = set()
    pattern = re.compile(r"^\s*([A-Za-z0-9_.-]+)")
    for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = pattern.match(line)
        if match:
            packages.add(match.group(1).lower().replace("_", "-"))
    return packages


def third_party_imports() -> set[str]:
    local = {path.name for path in SOURCE_ROOT.iterdir() if path.is_dir()}
    local.update(path.stem for path in SOURCE_ROOT.glob("*.py"))
    return {name for name in imported_modules()
            if name not in sys.stdlib_module_names and name not in local}


def main() -> int:
    declared = declared_packages()
    required = {IMPORT_TO_PACKAGE.get(name, name).lower().replace("_", "-")
                for name in third_party_imports()}
    missing = sorted(required - declared)
    if missing:
        print("requirements.txt is missing packages for imports: %s" % ", ".join(missing))
        print("Update seedrfetch/requirements.txt and AGENTS.md, then add a CHANGELOG.md entry.")
        return 1
    print("OK: requirements.txt covers all third-party imports (%d packages)." % len(required))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
