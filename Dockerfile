# Use official Python image
FROM python:3.10-slim

# Set work directory
WORKDIR /app

# Copy backend code
COPY backend/ ./backend/
COPY start.sh ./

# Install dependencies
RUN pip install --upgrade pip \
    && pip install -r backend/requirements.txt

# Make start.sh executable
RUN chmod +x start.sh

# Expose port
EXPOSE 5000

# Start the app
CMD ["./start.sh"] 