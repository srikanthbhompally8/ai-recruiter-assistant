"""Database Integrity Verification Script"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models import Base
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_database_integrity():
    """Verify database schema and data integrity"""

    print("\n" + "="*70)
    print("DATABASE INTEGRITY VERIFICATION")
    print("="*70)
    print(f"Timestamp: {datetime.now().isoformat()}\n")

    engine = create_engine(settings.DATABASE_URL, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    results = {
        "checks_passed": 0,
        "checks_failed": 0,
        "warnings": []
    }

    try:
        # Check 1: Database connectivity
        print("[CHECK 1] Database Connectivity")
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            print("  [OK] Database is accessible\n")
            results["checks_passed"] += 1
        except Exception as e:
            print(f"  [FAIL] Cannot connect to database: {e}\n")
            results["checks_failed"] += 1
            return results

        # Check 2: Table existence
        print("[CHECK 2] All Required Tables Exist")
        inspector = inspect(engine)
        existing_tables = set(inspector.get_table_names())
        required_tables = {
            "users", "candidates", "job_descriptions", "matches",
            "skill_taxonomy"
        }

        missing_tables = required_tables - existing_tables
        if missing_tables:
            print(f"  [FAIL] Missing tables: {missing_tables}\n")
            results["checks_failed"] += 1
        else:
            print(f"  [OK] All {len(required_tables)} required tables exist\n")
            results["checks_passed"] += 1

        # Check 3: Foreign key relationships
        print("[CHECK 3] Foreign Key Relationships")
        try:
            # Check candidates.user_id references users.id
            candidate_count = session.execute(
                text("SELECT COUNT(*) FROM candidates")
            ).scalar()
            valid_user_refs = session.execute(
                text("SELECT COUNT(*) FROM candidates c WHERE c.user_id IN (SELECT id FROM users)")
            ).scalar()

            if candidate_count == valid_user_refs:
                print(f"  [OK] Candidates -> Users: {valid_user_refs}/{candidate_count} valid references")
                results["checks_passed"] += 1
            else:
                print(f"  [WARN] Some candidate user references may be invalid")
                results["warnings"].append("Invalid candidate->user references")

            # Check job_descriptions.user_id references users.id
            job_count = session.execute(
                text("SELECT COUNT(*) FROM job_descriptions")
            ).scalar()
            valid_job_refs = session.execute(
                text("SELECT COUNT(*) FROM job_descriptions j WHERE j.user_id IN (SELECT id FROM users)")
            ).scalar()

            if job_count == valid_job_refs:
                print(f"  [OK] Job Descriptions -> Users: {valid_job_refs}/{job_count} valid references")
            else:
                print(f"  [WARN] Some job user references may be invalid")
                results["warnings"].append("Invalid job->user references")

            # Check matches references
            match_count = session.execute(
                text("SELECT COUNT(*) FROM matches")
            ).scalar()
            valid_match_refs = session.execute(
                text("""
                SELECT COUNT(*) FROM matches m
                WHERE m.candidate_id IN (SELECT id FROM candidates)
                AND m.job_id IN (SELECT id FROM job_descriptions)
                """)
            ).scalar()

            if match_count == valid_match_refs:
                print(f"  [OK] Matches: {valid_match_refs}/{match_count} have valid references\n")
                results["checks_passed"] += 1
            else:
                print(f"  [WARN] Some match references may be invalid\n")
                results["warnings"].append("Invalid match references")

        except Exception as e:
            print(f"  [FAIL] Foreign key check error: {e}\n")
            results["checks_failed"] += 1

        # Check 4: Data consistency
        print("[CHECK 4] Data Consistency")
        try:
            # Check no NULL in required fields
            null_emails = session.execute(
                text("SELECT COUNT(*) FROM users WHERE email IS NULL")
            ).scalar()

            null_candidates = session.execute(
                text("SELECT COUNT(*) FROM candidates WHERE email IS NULL OR full_name IS NULL")
            ).scalar()

            null_jobs = session.execute(
                text("SELECT COUNT(*) FROM job_descriptions WHERE title IS NULL")
            ).scalar()

            if null_emails == 0 and null_candidates == 0 and null_jobs == 0:
                print(f"  [OK] No NULL values in required fields")
                results["checks_passed"] += 1
            else:
                print(f"  [WARN] Found NULL values in required fields")
                results["checks_failed"] += 1

            # Check data record counts
            print(f"\n  Data Summary:")
            print(f"    - Users: {session.execute(text('SELECT COUNT(*) FROM users')).scalar()}")
            print(f"    - Candidates: {session.execute(text('SELECT COUNT(*) FROM candidates')).scalar()}")
            print(f"    - Jobs: {session.execute(text('SELECT COUNT(*) FROM job_descriptions')).scalar()}")
            print(f"    - Matches: {session.execute(text('SELECT COUNT(*) FROM matches')).scalar()}")
            print(f"    - Skills: {session.execute(text('SELECT COUNT(*) FROM skill_taxonomy')).scalar()}\n")

        except Exception as e:
            print(f"  [FAIL] Data consistency check error: {e}\n")
            results["checks_failed"] += 1

        # Check 5: Column constraints
        print("[CHECK 5] Column Constraints")
        try:
            # Check unique constraints
            duplicate_emails = session.execute(
                text("SELECT COUNT(*) FROM (SELECT email, COUNT(*) as cnt FROM users GROUP BY email HAVING cnt > 1) t")
            ).scalar()

            if duplicate_emails == 0:
                print(f"  [OK] Email uniqueness constraint maintained")
                results["checks_passed"] += 1
            else:
                print(f"  [FAIL] Found {duplicate_emails} duplicate emails")
                results["checks_failed"] += 1

            print()

        except Exception as e:
            print(f"  [WARN] Constraint check error: {e}\n")

        # Check 6: Schema validation
        print("[CHECK 6] Schema Validation")
        try:
            # Verify expected columns exist
            users_cols = {col.name for col in inspector.get_columns("users")}
            required_user_cols = {"id", "email", "password_hash", "full_name", "role"}

            if required_user_cols.issubset(users_cols):
                print(f"  [OK] Users table has all required columns")
                results["checks_passed"] += 1
            else:
                missing = required_user_cols - users_cols
                print(f"  [FAIL] Users table missing columns: {missing}")
                results["checks_failed"] += 1

            candidates_cols = {col.name for col in inspector.get_columns("candidates")}
            required_cand_cols = {"id", "user_id", "email", "full_name"}

            if required_cand_cols.issubset(candidates_cols):
                print(f"  [OK] Candidates table has all required columns")
            else:
                missing = required_cand_cols - candidates_cols
                print(f"  [FAIL] Candidates table missing columns: {missing}")
                results["checks_failed"] += 1

            jobs_cols = {col.name for col in inspector.get_columns("job_descriptions")}
            required_job_cols = {"id", "user_id", "title", "description"}

            if required_job_cols.issubset(jobs_cols):
                print(f"  [OK] Job Descriptions table has all required columns\n")
                results["checks_passed"] += 1
            else:
                missing = required_job_cols - jobs_cols
                print(f"  [FAIL] Job table missing columns: {missing}\n")
                results["checks_failed"] += 1

        except Exception as e:
            print(f"  [FAIL] Schema validation error: {e}\n")
            results["checks_failed"] += 1

    finally:
        session.close()

    # Print summary
    print("="*70)
    print("VERIFICATION SUMMARY")
    print("="*70)
    total = results["checks_passed"] + results["checks_failed"]
    pass_rate = (results["checks_passed"] / total * 100) if total > 0 else 0

    print(f"Checks Passed: {results['checks_passed']}/{total}")
    print(f"Checks Failed: {results['checks_failed']}/{total}")
    print(f"Pass Rate: {pass_rate:.1f}%")

    if results["warnings"]:
        print(f"\nWarnings:")
        for warning in results["warnings"]:
            print(f"  - {warning}")

    print("="*70 + "\n")

    if results["checks_failed"] == 0:
        print("[OK] DATABASE INTEGRITY VERIFIED - ALL CHECKS PASSED\n")
        return True
    else:
        print(f"[FAIL] {results['checks_failed']} CHECK(S) FAILED\n")
        return False


if __name__ == "__main__":
    success = verify_database_integrity()
    exit(0 if success else 1)
