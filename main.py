import logging
import os
import random
import sys
import time

from flask import Flask, jsonify, request
from google.cloud import firestore
from pythonjsonlogger.json import JsonFormatter

# Configure observability
# with JSON Logging
logger = logging.getLogger()
logHandler = logging.StreamHandler(sys.stdout)
# Let's include 'trace_id' in the format
formatter = JsonFormatter(
    "%(actime)s %(levelname)s %(message)s %(component)s %(trace_id)s"
)
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

app = Flask(__name__)

project_id = os.environ.get("PROJECT_ID")
database_id = os.environ.get("DATABASE_ID", "(default)")

# Globals
GLOBAL_CACHE: dict | None = None  # use to demonstrate cold vs warm start logging

# setup firestore
try:
    db = firestore.Client(
        project=project_id,
        database=database_id,
    )
except Exception as e:
    logger.error(
        f"Failed to init Firestore in project: {project_id}", extra={"error": str(e)}
    )
    db = None


def get_trace_id():
    """Helper to link logs to Cloud Trace"""
    trace_header = request.headers.get("X-Cloud-Trace-Context")
    if trace_header and "/" in trace_header:
        return trace_header.split("/")[0]


@app.route("/")
def welcome():
    logger.info(
        "Root endpoint called",
        extra={"component": "traffic", "trace_id": get_trace_id()},
    )
    return "Cloud Run Demo App is Online!", 200


# db activity
@app.route("/users", methods=["POST"])
def add_user():
    """
    Show logs and DB interaction
    """
    data = request.json()
    user_id = data.get("id")
    name = data.get("name")

    if not user_id or not name:
        logger.error(
            "Invalid input",
            extra={
                "component": "user-module",
                "input": data,
                "trace_id": get_trace_id(),
            },
        )
        return jsonify({"message": "Missing ID or Name"}), 400

    if db:
        doc_ref = db.collection("sampleUsers").document(str(user_id))
        doc_ref.set({"name": name, "timestamp": firestore.SERVER_TIMESTAMP})

    logger.info(
        "User created",
        extra={
            "component": "user-module",
            "user_id": user_id,
            "trace_id": get_trace_id(),
        },
    )
    return jsonify({"message": "Created successfully"}), 201


# demonstrate latency
@app.route("/slow-trace", methods=["GET"])
def slow_request():
    """
    Simulate a slow dependency.
    This allows us to show a 'Trace List' in GCP
    """
    trace_id = get_trace_id()
    logger.info(
        "Starting slow process...",
        extra={"component": "trace-demo", "trace_id": trace_id},
    )

    # simulate slow processing
    time.sleep(4)

    # simulate db call to show firestore in trace
    if db:
        docs = db.collection("newUsers").limit(1).stream()
        for doc in docs:
            pass

    logger.info(
        "Slow process finished...",
        extra={"component": "trace-demo", "trace_id": trace_id},
    )

    return jsonify({"message": " Sorry, I am just simulating latency!"}), 200


# demonstrate metrics & concurrency
@app.route("/cpu-heavy", methods=["GET"])
def cpu_heavy():
    """
    Calculate Fibonacci to spike the CPU.
    Hit this heavily to see the chart spike in the metrics for 'Container CPU Utilization'
    """
    logger.info(
        "Starting CPU crunch",
        extra={"component": "cpu-demo", "trace_id": get_trace_id()},
    )

    def fib(n):
        if n <= 1:
            return n
        return fib(n - 1) + fib(n - 2)

    result = fib(30)  # high enough to spike CPU

    return jsonify({"result": result}), 200


# errors and alerts
@app.route("/flaky", methods=["GET"])
def flaky_endpoint():
    """
    Randomly return a 500 error.
    Trigger error reporting or an alert policy
    """
    if random.choice([True, False]):
        logger.error(
            "Random Chaos Monkey Struck!",
            extra={"component": "chaos", "trace_id": get_trace_id()},
        )
        return jsonify({"message": "Internal Server Error"}), 500

    return jsonify({"status": "Wheew! I survived"})


@app.route("/cached-config", methods=["GET"])
def cached_config():
    """
    Demonstrate logs that difference in cold vs warm starts
    Filter logs where 'jsonPayload.component="cache"'
    """
    global GLOBAL_CACHE
    trace_id = get_trace_id()

    if GLOBAL_CACHE is None:
        logger.info(
            "Cache Miss - Fetching Config...",
            extra={"component": "cache", "trace_id": trace_id},
        )
        time.sleep(2)  # simulate some load handling
        GLOBAL_CACHE = {"theme": "dark", "version": "0.0.1"}
    else:
        logger.info(
            "Cache Hit - Serving from RAM",
            extra={"component": "cacje", "trace_id": trace_id},
        )

    return jsonify(GLOBAL_CACHE)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
