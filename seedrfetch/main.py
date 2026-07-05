"""SeedrFetch entry point. Logging and OS trust initialize before Requests."""
import argparse
import os
import sys
from pathlib import Path


def ensure_project_interpreter() -> None:
    """Relaunch with the workspace's Python 3.13 environment when available."""
    project_python = (Path(__file__).resolve().parents[1] /
                      "rwakiDev_v3" / "Scripts" / "python.exe")
    if not project_python.is_file():
        return
    try:
        current = Path(sys.executable).resolve()
        expected = project_python.resolve()
    except OSError:
        return
    if current != expected:
        os.execv(str(expected), [str(expected), str(Path(__file__).resolve()), *sys.argv[1:]])


def main() -> None:
    ensure_project_interpreter()
    parser = argparse.ArgumentParser(description="SeedrFetch")
    parser.add_argument("--debug", action="store_true", help="enable DEBUG console logging")
    args = parser.parse_args()
    from core.logging_setup import setup_logging
    logger = setup_logging(args.debug)
    from core import ssl_setup  # noqa: F401
    from core.config import Config
    try:
        from ui.app import App
    except ImportError as exc:
        raise SystemExit(f"Missing dependency: {exc}. Run: python -m pip install -r requirements.txt") from exc
    app = App(Config(), logger)
    try:
        app.mainloop()
    except KeyboardInterrupt:
        logger.info("Interrupted by user (Ctrl+C). Shutting down.")
        try:
            app.destroy()
        except Exception:
            pass


if __name__ == "__main__":
    main()
