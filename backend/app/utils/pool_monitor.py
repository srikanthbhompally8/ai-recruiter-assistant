"""Connection Pool Monitoring Utilities"""

from sqlalchemy import event
from sqlalchemy.pool import Pool
import logging
import time
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

class PoolMonitor:
    """Monitors database connection pool statistics"""

    def __init__(self):
        self.created = 0
        self.checked_out = 0
        self.checked_in = 0
        self.overflow_created = 0
        self.start_time = datetime.now()
        self.events = []

    def register_listeners(self, engine):
        """Register event listeners on SQLAlchemy engine"""

        @event.listens_for(engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            self.created += 1
            self.events.append({
                "type": "connect",
                "timestamp": datetime.now().isoformat(),
                "total_created": self.created
            })
            logger.debug(f"Pool: Connection created (total: {self.created})")

        @event.listens_for(engine, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            self.checked_out += 1
            # Track the peak number of overflow connections in use (valid pool state, not an event)
            overflow = engine.pool.overflow()
            if overflow > self.overflow_created:
                self.overflow_created = overflow
                logger.warning(f"Pool: Overflow connections in use: {overflow}")
            logger.debug(f"Pool: Connection checked out (active: {self.checked_out})")

        @event.listens_for(engine, "checkin")
        def receive_checkin(dbapi_conn, connection_record):
            self.checked_in += 1
            self.checked_out = max(0, self.checked_out - 1)
            logger.debug(f"Pool: Connection returned (active: {self.checked_out})")


        @event.listens_for(Pool, "close")
        def receive_close(dbapi_conn, connection_record):
            logger.debug("Pool: Connection closed")

    def get_stats(self) -> Dict[str, Any]:
        """Get current pool statistics"""
        uptime = (datetime.now() - self.start_time).total_seconds()

        return {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": round(uptime, 2),
            "total_connections_created": self.created,
            "active_checkouts": self.checked_out,
            "total_checkins": self.checked_in,
            "overflow_connections": self.overflow_created,
            "health": "healthy" if self.overflow_created == 0 else "warning"
        }

    def reset(self):
        """Reset all counters"""
        self.created = 0
        self.checked_out = 0
        self.checked_in = 0
        self.overflow_created = 0
        self.start_time = datetime.now()
        self.events = []

# Global monitor instance
_monitor = None

def init_monitor(engine) -> PoolMonitor:
    """Initialize the pool monitor"""
    global _monitor
    _monitor = PoolMonitor()
    _monitor.register_listeners(engine)
    logger.info("Connection pool monitoring initialized")
    return _monitor

def get_monitor() -> PoolMonitor:
    """Get the global monitor instance"""
    if _monitor is None:
        raise RuntimeError("Pool monitor not initialized. Call init_monitor(engine) first.")
    return _monitor
