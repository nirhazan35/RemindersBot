import logging
from fastapi import APIRouter

logging.basicConfig(level=logging.INFO)

router = APIRouter()

@router.get("/health")
async def health_check():
    logging.info("Health check endpoint was called")
    return {"status": "ok"}
