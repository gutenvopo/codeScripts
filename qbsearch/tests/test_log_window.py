from __future__ import annotations

import logging
import queue

from qbsearch.ui.log_window import VerboseLogHandler


def test_verbose_log_handler_queues_selected_records_without_tk() -> None:
    messages: queue.SimpleQueue[tuple[int, str]] = queue.SimpleQueue()
    handler = VerboseLogHandler(messages, ("qbsearch.core.magnet_resolver",))
    handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))

    included = logging.LogRecord(
        "qbsearch.core.magnet_resolver",
        logging.ERROR,
        __file__,
        1,
        "HTTP %s",
        (503,),
        None,
    )
    excluded = logging.LogRecord(
        "qbsearch.core.search_controller",
        logging.INFO,
        __file__,
        1,
        "not shown",
        (),
        None,
    )

    handler.emit(included)
    handler.emit(excluded)

    assert messages.get_nowait() == (logging.ERROR, "ERROR HTTP 503")
    assert messages.empty()
