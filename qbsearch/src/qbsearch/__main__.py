from __future__ import annotations

import logging

import truststore

from qbsearch.app import QbSearchApp
from qbsearch.logging_setup import setup_logging
from qbsearch.version import APP_NAME, __version__


def main() -> None:
    truststore.inject_into_ssl()
    setup_logging()
    logging.getLogger(__name__).info("starting %s %s", APP_NAME, __version__)
    app = QbSearchApp()
    app.mainloop()


if __name__ == "__main__":
    main()
