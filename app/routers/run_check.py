import logging
from fastapi import APIRouter

logging.basicConfig(level=logging.INFO)

router = APIRouter()

@router.post("/run-check")
async def run_check():
    logging.info("Run check endpoint was called")
    bot = router.services["bot"]
    try:
        await bot.run_daily_check()
        logging.info("Daily check completed successfully")
        return {"status": "Check completed successfully"}
    except Exception as e:
        logging.error(f"Error during run-check: {e}")
        return {"status": "error", "message": str(e)}
