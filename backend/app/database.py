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
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,              # Default connections to maintain
    max_overflow=40,           # Max connections beyond pool_size
    pool_recycle=3600,         # Recycle connections after 1 hour
    pool_pre_ping=True,        # Test connections before use
    echo=ENABLE_QUERY_LOGGING, # Only log queries in dev mode
    connect_args={
        'timeout': 30,         # Connection timeout in seconds
        'check_same_thread': False  # SQLite specific (if used)
    }
)

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
