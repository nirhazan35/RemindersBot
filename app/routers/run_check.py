from fastapi import APIRouter

router = APIRouter()

@router.post("/run-check")
async def run_check():
    bot = router.services["bot"]
    try:
        await bot.run_daily_check()
        return {"status": "Check completed successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
