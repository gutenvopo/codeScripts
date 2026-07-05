"""Entry point for Student Data Extractor."""

from __future__ import annotations

from app import StudentDataExtractorApp


def main() -> None:
    """Start the desktop application."""

    app = StudentDataExtractorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
