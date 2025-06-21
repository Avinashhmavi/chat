#!/bin/bash
   cd backend
   source venv/Scripts/activate
   uvicorn app:app --port 5000