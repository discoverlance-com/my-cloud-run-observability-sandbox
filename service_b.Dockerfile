# Builder Stage
FROM python:3.11-slim AS builder
WORKDIR /app

COPY service_b.requirements.txt .
RUN pip install --no-cache-dir -r service_b.requirements.txt -t /app/site-packages

COPY service_b.py /app/main.py
COPY setup_opentelemetry.py /app/setup_opentelemetry.py
COPY setup_structured_logging.py /app/setup_structured_logging.py

# Runtime Stage
FROM gcr.io/distroless/python3-debian12

WORKDIR /app
ENV PYTHONPATH=/app/site-packages

COPY --from=builder /app/site-packages /app/site-packages
COPY --from=builder /app/main.py /app/main.py
COPY --from=builder /app/setup_opentelemetry.py /app/setup_opentelemetry.py
COPY --from=builder /app/setup_structured_logging.py /app/setup_structured_logging.py

USER nonroot

# we cannot execute the 'gunicorn' binary in distroless
# we instead execute the 'gunicorn' module directly with -m
CMD ["-m", "gunicorn", "--bind", ":8080", "--workers", "1", "--threads", "8", "--timeout", "0", "main:app"]
