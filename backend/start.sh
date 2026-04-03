#!/bin/bash
set -e

echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --timeout-keep-alive 5 --limit-concurrency 500
