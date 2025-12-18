import logging
from datetime import datetime
from typing import Optional

from opentelemetry.instrumentation.logging import LoggingInstrumentor
from pythonjsonlogger.json import JsonFormatter as PyJsonFormatter

# We override JsonFormatter.formatTime() instead of using the datefmt strftime parameter
# because it does not support microsecond precision.


# [START opentelemetry_instrumentation_setup_logging]
class JsonFormatter(PyJsonFormatter):
    def formatTime(self, record: logging.LogRecord, datefmt: Optional[str] = None):
        # Format the timestamp as RFC 3339 with microsecond precision
        isoformat = datetime.fromtimestamp(record.created).isoformat()
        return f"{isoformat}Z"


def setup_structured_logging() -> None:
    LoggingInstrumentor().instrument()

    log_handler = logging.StreamHandler()
    formatter = JsonFormatter(
        "%(asctime)s %(levelname)s $(component) %(message)s %(otelTraceID)s %(otelSpanID)s %(otelTraceSampled)s",
        rename_fields={
            "levelname": "severity",
            "asctime": "timestamp",
            "component": "type",
            "otelTraceID": "logging.googleapis.com/trace",
            "otelSpanID": "logging.googleapis.com/spanId",
            "otelTraceSampled": "logging.googleapis.com/trace_sampled",
        },
    )
    log_handler.setFormatter(formatter)
    logging.basicConfig(
        level=logging.INFO,
        handlers=[log_handler],
    )
