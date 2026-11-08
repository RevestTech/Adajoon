#!/bin/bash
# Run database migrations on Railway
cd backend && python -m alembic upgrade head
