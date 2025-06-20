#!/bin/bash
cd backend
uvicorn app:app --host 0.0.0.0 --port 5000 --reload &
uvicorn db_api:app --host 0.0.0.0 --port 8001 --reload &
cd ../frontend && python -m http.server 8000