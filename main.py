import json
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
