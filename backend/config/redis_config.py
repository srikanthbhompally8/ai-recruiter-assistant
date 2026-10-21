"""
Redis configuration settings
"""

import os
from dotenv import load_dotenv

load_dotenv()

REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', 'localhost'),
    'port': int(os.getenv('REDIS_PORT', 6379)),
    'db': int(os.getenv('REDIS_DB', 0)),
    'enabled': os.getenv('CACHE_ENABLED', 'true').lower() == 'true',
    'ttl': {
        'match': int(os.getenv('REDIS_TTL_MATCH', 300)),
        'rank': int(os.getenv('REDIS_TTL_RANK', 600)),
        'embedding': int(os.getenv('REDIS_TTL_EMBEDDING', 86400))
    }
}

__all__ = ['REDIS_CONFIG']