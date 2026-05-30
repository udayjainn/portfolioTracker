#!/bin/sh
# Worker + beat in one process (Phase 1 Railway / S4).
set -e
exec celery -A app.celery_app worker --beat --loglevel=info --concurrency="${CELERY_CONCURRENCY:-4}"
