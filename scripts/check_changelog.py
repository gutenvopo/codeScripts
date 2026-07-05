"""Require a changelog update whenever SeedrFetch Python code changes."""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def git_names(*args: str) -> set[str]:
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                            text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return {line.strip().replace("\\", "/") for line in result.stdout.splitlines()
            if line.strip()}


def changed_files() -> set[str]:
    staged = git_names("diff", "--cached", "--name-only", "--diff-filter=ACMRT")
    if staged:
        return staged
    unstaged = git_names("diff", "--name-only", "HEAD", "--diff-filter=ACMRT")
    untracked = git_names("ls-files", "--others", "--exclude-standard")
    return unstaged | untracked


def main() -> int:
    try:
        changed = changed_files()
    except RuntimeError as exc:
        print("Unable to inspect Git changes: %s" % exc)
        return 1
    python_changed = any(path.startswith("seedrfetch/") and path.endswith(".py")
                         for path in changed)
    if python_changed and "CHANGELOG.md" not in changed:
        print("CHANGELOG.md not updated. Add an entry under [Unreleased] for your change. "
              "See AGENTS.md → File-modification protocol.")
        return 1
    print("OK: changelog protocol satisfied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
