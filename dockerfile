FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy project files to the container
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8000
EXPOSE 8000

# Default command to run the FastAPI app
CMD ["uvicorn", "rest_api:app", "--host", "0.0.0.0", "--port", "8000"]
