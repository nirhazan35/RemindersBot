from fastapi import FastAPI
from app.initialization import initialize_services
from app.routers import webhook, run_check, health

app = FastAPI()

# Initialize services (config, DB, custom classes, etc.)
services = initialize_services()

# Make the services accessible inside each router (simple approach).
webhook.router.services = services
run_check.router.services = services
health.router.services = services

# Include our routers in the main FastAPI app.
app.include_router(webhook.router)
app.include_router(run_check.router)
app.include_router(health.router)
