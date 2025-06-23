#!/bin/bash
cd backend
# Activate venv if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi
# Run uvicorn on all interfaces for Docker
exec uvicorn app:app --host 0.0.0.0 --port 5000