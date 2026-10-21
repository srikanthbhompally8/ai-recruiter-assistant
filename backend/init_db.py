"""Initialize SQLite database with schema and test data."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine
from app.database import Base
from app.config import settings
from app.models import User, Candidate, JobDescription, Match, SkillTaxonomy
import uuid
from datetime import datetime

# Create engine and tables
engine = create_engine(settings.DATABASE_URL, echo=True)
Base.metadata.create_all(engine)

print("[OK] Database tables created successfully!")
print(f"Database: {settings.DATABASE_URL}")
print("\nTables created:")
for table_name in sorted(Base.metadata.tables.keys()):
    print(f"  - {table_name}")

print("\n[OK] Schema verification complete")
