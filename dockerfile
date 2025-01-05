FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Create a non-root user
RUN useradd -m nonrootuser
USER nonrootuser

# Copy application files
COPY --chown=nonrootuser:nonrootuser . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Add ~/.local/bin to PATH
ENV PATH="/home/nonrootuser/.local/bin:$PATH"

# Expose port 8000
EXPOSE 8000

# Default command
CMD ["uvicorn", "app.rest_api:app", "--host", "0.0.0.0", "--port", "8000"]
