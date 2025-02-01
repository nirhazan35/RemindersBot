# --------------------------
# 1) BUILD/TEST STAGE
# --------------------------
    FROM python:3.9-slim AS build

    # Create and switch to the /app directory
    WORKDIR /app
    
    # Copy requirements first to leverage Docker layer caching
    COPY requirements.txt ./
    
    # Install required Python packages (including dev dependencies if needed for testing)
    RUN pip install --no-cache-dir -r requirements.txt
    
    # Copy the entire codebase into /app
    COPY . /app
    
    # Now run tests. If any test fails, this Docker build will fail and stop here.
    RUN pytest --maxfail=1 --disable-warnings -v
    
    # --------------------------
    # 2) PRODUCTION STAGE
    # --------------------------
    FROM python:3.9-slim AS production
    
    WORKDIR /app
    
    # Copy the application code from the build stage
    COPY --from=build /app /app
    
    # Install (production) dependencies. If you have separate dev vs. prod reqs, adjust accordingly.
    RUN pip install --no-cache-dir -r requirements.txt
    
    # Expose the port (if you're using 8000 in Render, for example)
    EXPOSE 8000
    
    # Start the FastAPI app with uvicorn
    CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
    