"""Database Configuration and Setup"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import QueuePool
from app.config import settings
import logging

logging.basicConfig()
logger = logging.getLogger(__name__)

# Only enable query logging in development
ENABLE_QUERY_LOGGING = settings.DEBUG and settings.ENVIRONMENT == "development"

if ENABLE_QUERY_LOGGING:
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)


def _build_engine():
    """Create the engine with dialect-appropriate options.

    PostgreSQL uses a pooled connection (pool sizes from settings).
    SQLite (local dev) does not support the pool arguments or the psycopg2
    connect options, so it is configured separately.
    """
    if settings.DATABASE_URL.startswith("sqlite"):
        return create_engine(
            settings.DATABASE_URL,
            echo=ENABLE_QUERY_LOGGING,
            connect_args={"check_same_thread": False},
        )

    return create_engine(
        settings.DATABASE_URL,
        poolclass=QueuePool,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_recycle=settings.DB_POOL_RECYCLE,
        pool_pre_ping=settings.DB_POOL_PRE_PING,
        echo=ENABLE_QUERY_LOGGING,
        connect_args={"connect_timeout": settings.DB_CONNECTION_TIMEOUT},
    )


engine = _build_engine()

# Initialize pool monitoring
try:
    from app.utils.pool_monitor import init_monitor

    pool_monitor = init_monitor(engine)
except Exception as e:
    logger.warning(f"Could not initialize pool monitor: {e}")

# Session Factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base Class for Models
Base = declarative_base()


def get_db():
    """Dependency for FastAPI to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


async def close_db():
    """Close database connection"""
    engine.dispose()
