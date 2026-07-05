import importlib
import sys

MODULES_TO_TEST = [
    "pandas",
    "requests",
    "bs4",
    "PIL",
    "psutil",
    "speedtest",
]


def main() -> int:
    print("=== Python Import Test ===")
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version.split()[0]}")
    print("--------------------------")

    failures = []

    for module_name in MODULES_TO_TEST:
        try:
            module = importlib.import_module(module_name)
            module_version = getattr(module, "__version__", "unknown")
            print(f"[PASS] {module_name:<10} version={module_version}")
        except Exception as error:
            failures.append((module_name, error))
            print(f"[FAIL] {module_name:<10} error={error}")

    print("--------------------------")
    if failures:
        print(f"Import test finished: {len(failures)} failed, {len(MODULES_TO_TEST) - len(failures)} passed")
        return 1

    print(f"Import test finished: all {len(MODULES_TO_TEST)} imports passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
