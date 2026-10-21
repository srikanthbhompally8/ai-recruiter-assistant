"""Health Check Endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from app.database import get_db
from sqlalchemy.orm import Session
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "Service is running",
    }


@router.get("/pool-stats")
async def get_pool_stats(db: Session = Depends(get_db)):
    """Get connection pool statistics (admin only)"""
    try:
        from app.utils.pool_monitor import get_monitor

        monitor = get_monitor()
        return {"status": "success", "pool_statistics": monitor.get_stats()}
    except Exception as e:
        logger.error(f"Error getting pool stats: {e}")
        raise HTTPException(
            status_code=500, detail="Could not retrieve pool statistics"
        )
