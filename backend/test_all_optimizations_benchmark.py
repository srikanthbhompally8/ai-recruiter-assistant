"""
Comprehensive Optimization Benchmark
Measures performance improvements from all Priority 2 optimizations
"""

import time
import json
import logging
from datetime import datetime
from app.database import SessionLocal
from app.utils.performance_tracker import PerformanceTracker, ComparisonAnalyzer, get_tracker
from sqlalchemy import text
from app.models import Match, Candidate, JobDescription

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptimizationBenchmark:
    """Benchmark all optimizations together"""

    def __init__(self):
        self.results = {}

    def benchmark_connection_pool(self):
        """Benchmark connection pool reuse performance"""
        logger.info("\n" + "="*60)
        logger.info("BENCHMARK: Connection Pool Reuse")
        logger.info("="*60)

        tracker = get_tracker("connection_pool")
        tracker.reset()

        # Run 100 queries to measure pool efficiency
        for i in range(100):
            start = time.time()
            try:
                db = SessionLocal()
                result = db.execute(text("SELECT 1 as test")).fetchone()
                duration = (time.time() - start) * 1000

                db.close()

                tracker.record_query(f"pool_query_{i}", duration, "/pool_test")
            except Exception as e:
                tracker.record_query(f"pool_query_{i}", 0, "/pool_test", "error", str(e))

        stats = tracker.get_statistics()
        logger.info(f"✅ Average Connection Time: {stats.avg_query_time_ms}ms")
        logger.info(f"✅ P95 Time: {stats.p95_query_time_ms}ms")
        logger.info(f"✅ Throughput: {stats.queries_per_second} q/s")

        return tracker.generate_report()

    def benchmark_matches_endpoint(self):
        """Benchmark matches endpoint (with N+1 fix)"""
        logger.info("\n" + "="*60)
        logger.info("BENCHMARK: Matches Endpoint (ORM Optimized)")
        logger.info("="*60)

        db = SessionLocal()

        try:
            # Get a job to test
            job = db.query(JobDescription).first()
            if not job:
                logger.warning("No jobs found - skipping matches benchmark")
                return None

            tracker = get_tracker("matches_endpoint")
            tracker.reset()

            # Run 50 match queries
            for i in range(50):
                start = time.time()
                try:
                    # This uses the optimized join query
                    matches_data = db.query(Match, Candidate).join(
                        Candidate, Match.candidate_id == Candidate.id
                    ).filter(Match.job_id == job.id).limit(50).all()

                    duration = (time.time() - start) * 1000
                    tracker.record_query(f"matches_query_{i}", duration, f"/matches/{job.id}")

                except Exception as e:
                    logger.error(f"Error in matches query: {e}")
                    tracker.record_query(f"matches_query_{i}", 0, f"/matches/{job.id}", "error", str(e))

            stats = tracker.get_statistics()
            logger.info(f"✅ Average Query Time: {stats.avg_query_time_ms}ms")
            logger.info(f"✅ P95 Time: {stats.p95_query_time_ms}ms")
            logger.info(f"✅ Success Rate: {100 - stats.error_rate}%")

            return tracker.generate_report()

        finally:
            db.close()

    def benchmark_candidate_ranking(self):
        """Benchmark candidate ranking (with batch processing)"""
        logger.info("\n" + "="*60)
        logger.info("BENCHMARK: Candidate Ranking (Batch Optimized)")
        logger.info("="*60)

        db = SessionLocal()

        try:
            tracker = get_tracker("candidate_ranking")
            tracker.reset()

            # Get a job
            job = db.query(JobDescription).first()
            if not job:
                logger.warning("No jobs found - skipping ranking benchmark")
                return None

            # Run batch processing test
            for batch_num in range(3):
                start = time.time()
                try:
                    batch_size = 100
                    offset = batch_num * batch_size

                    candidates = db.query(Candidate).limit(batch_size).offset(offset).all()

                    duration = (time.time() - start) * 1000
                    tracker.record_query(
                        f"ranking_batch_{batch_num}",
                        duration,
                        f"/ranking/{job.id}?batch={batch_num}"
                    )

                    if not candidates:
                        break

                except Exception as e:
                    logger.error(f"Error in ranking: {e}")
                    tracker.record_query(
                        f"ranking_batch_{batch_num}",
                        0,
                        f"/ranking/{job.id}?batch={batch_num}",
                        "error",
                        str(e)
                    )

            stats = tracker.get_statistics()
            logger.info(f"✅ Average Batch Time: {stats.avg_query_time_ms}ms")
            logger.info(f"✅ P95 Time: {stats.p95_query_time_ms}ms")
            logger.info(f"✅ Success Rate: {100 - stats.error_rate}%")

            return tracker.generate_report()

        finally:
            db.close()

    def run_all_benchmarks(self):
        """Run all benchmarks and generate summary"""
        logger.info("\n" + "="*70)
        logger.info("COMPREHENSIVE OPTIMIZATION BENCHMARK")
        logger.info("Measuring all Phase 4 Priority 2 Optimizations")
        logger.info("="*70)

        benchmarks = {
            "connection_pool": self.benchmark_connection_pool(),
            "matches_endpoint": self.benchmark_matches_endpoint(),
            "candidate_ranking": self.benchmark_candidate_ranking(),
        }

        # Filter out None results
        benchmarks = {k: v for k, v in benchmarks.items() if v is not None}

        return benchmarks

    def print_summary(self, benchmarks):
        """Print benchmark summary"""
        logger.info("\n" + "="*70)
        logger.info("BENCHMARK SUMMARY")
        logger.info("="*70)

        for name, report in benchmarks.items():
            summary = report["summary"]
            logger.info(f"\n{name.upper()}:")
            logger.info(f"  Total Queries: {summary['total_queries']}")
            logger.info(f"  Avg Query Time: {summary['avg_query_time_ms']}ms")
            logger.info(f"  P95 Query Time: {summary['p95_query_time_ms']}ms")
            logger.info(f"  Throughput: {summary['queries_per_second']} q/s")
            logger.info(f"  Error Rate: {summary['error_rate']}%")

        logger.info("\n" + "="*70)

def main():
    """Run comprehensive benchmark"""
    benchmark = OptimizationBenchmark()
    benchmarks = benchmark.run_all_benchmarks()
    benchmark.print_summary(benchmarks)

    # Save results
    final_report = {
        "report_name": "Comprehensive Optimization Benchmark",
        "timestamp": datetime.now().isoformat(),
        "benchmarks": benchmarks,
        "optimizations_included": [
            "ORM Query Optimization (N+1 fixes)",
            "Batch Processing (Candidate Ranking)",
            "Connection Pool Reuse"
        ]
    }

    with open("OPTIMIZATION_BENCHMARK_RESULTS.json", "w") as f:
        json.dump(final_report, f, indent=2)

    logger.info("\n✅ Results saved to: OPTIMIZATION_BENCHMARK_RESULTS.json\n")

    return final_report

if __name__ == "__main__":
    main()
