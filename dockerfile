# Use the official lightweight Python image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Create a non-root user and switch to it
RUN useradd -m nonrootuser
USER nonrootuser

# Copy the application files to the working directory
COPY --chown=nonrootuser:nonrootuser . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8000 for the app
EXPOSE 8000

# Default command to run the FastAPI app
CMD ["uvicorn", "rest_api:app", "--host", "0.0.0.0", "--port", "8000"]
