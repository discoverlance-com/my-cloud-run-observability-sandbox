# Builder Stage
FROM python:3.11-slim AS builder
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -t /app/site-packages

COPY main.py /app/main.py

# Runtime Stage
FROM gcr.io/distroless/python3-debian12

WORKDIR /app
ENV PYTHONPATH=/app/site-packages

COPY --from=builder /app/site-packages /app/site-packages
COPY --from=builder /app/main.py /app/main.py

USER nonroot

# we cannot execute the 'gunicorn' binary in distroless
# we instead execute the 'gunicorn' module directly with -m
CMD ["-m", "gunicorn", "--bind", ":8080", "--workers", "1", "--threads", "8", "--timeout", "0", "main:app"]
