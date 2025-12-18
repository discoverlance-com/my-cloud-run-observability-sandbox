import logging
import time
from random import randint, uniform

import requests
from flask import Flask, jsonify, request, url_for
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

from setup_opentelemetry import setup_opentelemetry
from setup_structured_logging import setup_structured_logging

logger = logging.getLogger(__name__)

# Initialize OpenTelemetry Python SDK and structured logging
setup_opentelemetry()
setup_structured_logging()

app = Flask(__name__)

# Add instrumentation
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()


@app.route("/multi")
def multi():
    """Handle an http request by making 3-7 http requests to the /single endpoint."""
    sub_requests = randint(3, 7)
    logger.info(
        "handle /multi request",
        extra={"subRequests": sub_requests, "component": "multi"},
    )
    for _ in range(sub_requests):
        requests.get(url_for("single", _external=True))
    return "ok"


@app.route("/multiply", methods=["POST"])
def multiply():
    data = request.get_json(silent=True)
    if data is None:
        logger.warning(
            "NO JSON body received in /multiply request",
            extra={"component": "multiply"},
        )
        data = {}
    val = data.get("value", 1)

    # simulate some work
    delay = uniform(0.1, 0.5)
    logger.info(
        "Handling /multiply request", extra={"delay": delay, "component": "multiply"}
    )
    time.sleep(delay)

    logger.info(f"Math service processed: {val}", extra={"component": "multiply"})

    return jsonify({"result": val * 2, "delay": delay}), 200


@app.route("/single")
def single():
    """Handle an http request by sleeping for 100-200 ms, and write the number of seconds slept as the response."""
    duration = uniform(0.1, 0.2)
    logger.info(
        "handle /single request", extra={"duration": duration, "component": "single"}
    )
    time.sleep(duration)
    return f"slept {duration} seconds"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
