FROM python:3.9-slim

# Create and switch to the /app directory
WORKDIR /app

# Copy requirements for pip install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy your entire app
COPY . /app

# Ensure environment variables are loaded
ENV PYTHONUNBUFFERED=1

# Expose the port (if you're using 8000 in Render, for example)
EXPOSE 8000

# Use a shell form CMD to allow variable expansion
CMD uvicorn app.main:app --host 0.0.0.0 --port 8000
