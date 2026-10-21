"""
Connection Pool Load Testing
Tests connection pooling under concurrent load
"""

import time
import json
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from sqlalchemy import text
from app.database import SessionLocal
from app.utils.pool_monitor import get_monitor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PoolLoadTest:
    """Load test connection pooling"""

    def __init__(self):
        self.results = []
        self.errors = []
        self.start_time = None
        self.end_time = None

    def simple_query(self, query_id: int) -> dict:
        """Execute a simple query using a connection from the pool"""
        try:
            db = SessionLocal()
            start = time.time()

            result = db.execute(text("SELECT 1 as test")).fetchone()

            duration = time.time() - start

            db.close()

            return {
                "query_id": query_id,
                "status": "success",
                "duration_ms": round(duration * 1000, 2),
                "result": result[0] if result else None
            }
        except Exception as e:
            self.errors.append(str(e))
            return {
                "query_id": query_id,
                "status": "error",
                "error": str(e)
            }

    def run_load_test(self, num_workers: int, queries_per_worker: int) -> dict:
        """Run concurrent load test"""
        logger.info(f"\n{'='*60}")
        logger.info(f"LOAD TEST: {num_workers} concurrent workers")
        logger.info(f"Queries per worker: {queries_per_worker}")
        logger.info(f"Total queries: {num_workers * queries_per_worker}")
        logger.info(f"{'='*60}")

        self.results = []
        self.errors = []
        self.start_time = time.time()

        query_counter = 0

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = []

            for worker_id in range(num_workers):
                for query_num in range(queries_per_worker):
                    future = executor.submit(self.simple_query, query_counter)
                    futures.append(future)
                    query_counter += 1

            for future in as_completed(futures):
                result = future.result()
                self.results.append(result)

        self.end_time = time.time()

        # Calculate statistics
        successful = [r for r in self.results if r["status"] == "success"]
        failed = [r for r in self.results if r["status"] == "error"]

        if successful:
            durations = [r["duration_ms"] for r in successful]
            avg_duration = sum(durations) / len(durations)
            max_duration = max(durations)
            min_duration = min(durations)
        else:
            avg_duration = max_duration = min_duration = 0

        total_duration = self.end_time - self.start_time

        # Get pool monitor stats
        try:
            monitor = get_monitor()
            pool_stats = monitor.get_stats()
        except:
            pool_stats = None

        result = {
            "test_name": f"Load test: {num_workers} workers",
            "timestamp": datetime.now().isoformat(),
            "total_queries": len(self.results),
            "successful_queries": len(successful),
            "failed_queries": len(failed),
            "success_rate": f"{(len(successful) / len(self.results) * 100):.1f}%",
            "total_duration_seconds": round(total_duration, 2),
            "throughput_queries_per_second": round(len(successful) / total_duration, 2),
            "query_times": {
                "average_ms": round(avg_duration, 2),
                "min_ms": round(min_duration, 2),
                "max_ms": round(max_duration, 2)
            },
            "pool_stats": pool_stats,
            "errors": self.errors[:10]  # First 10 errors
        }

        return result

    def print_result(self, result: dict):
        """Print test result"""
        logger.info(f"\n{'='*60}")
        logger.info(f"TEST RESULTS")
        logger.info(f"{'='*60}")
        logger.info(f"Total Queries: {result['total_queries']}")
        logger.info(f"Successful: {result['successful_queries']}")
        logger.info(f"Failed: {result['failed_queries']}")
        logger.info(f"Success Rate: {result['success_rate']}")
        logger.info(f"\nPerformance:")
        logger.info(f"  Total Duration: {result['total_duration_seconds']}s")
        logger.info(f"  Throughput: {result['throughput_queries_per_second']} queries/sec")
        logger.info(f"  Avg Query Time: {result['query_times']['average_ms']}ms")
        logger.info(f"  Min Query Time: {result['query_times']['min_ms']}ms")
        logger.info(f"  Max Query Time: {result['query_times']['max_ms']}ms")

        if result['pool_stats']:
            logger.info(f"\nPool Statistics:")
            logger.info(f"  Total Connections Created: {result['pool_stats']['total_connections_created']}")
            logger.info(f"  Active Checkouts: {result['pool_stats']['active_checkouts']}")
            logger.info(f"  Overflow Connections: {result['pool_stats']['overflow_connections']}")
            logger.info(f"  Pool Health: {result['pool_stats']['health'].upper()}")

        if result['errors']:
            logger.warning(f"\nSample Errors ({len(result['errors'])}):")
            for error in result['errors'][:3]:
                logger.warning(f"  - {error}")

        logger.info(f"{'='*60}\n")

def main():
    """Run all load tests"""
    logger.info("Connection Pool Load Testing")
    logger.info("Testing database connection pooling under concurrent load\n")

    tester = PoolLoadTest()

    # Test scenarios
    test_scenarios = [
        (10, 5),    # 10 workers, 5 queries each = 50 total
        (20, 10),   # 20 workers, 10 queries each = 200 total
        (50, 5),    # 50 workers, 5 queries each = 250 total
        (100, 3),   # 100 workers, 3 queries each = 300 total (stress test)
    ]

    all_results = []

    for num_workers, queries_per_worker in test_scenarios:
        result = tester.run_load_test(num_workers, queries_per_worker)
        all_results.append(result)
        tester.print_result(result)
        time.sleep(1)  # Brief pause between tests

    # Generate summary report
    summary = {
        "test_suite": "Connection Pool Load Testing",
        "timestamp": datetime.now().isoformat(),
        "test_count": len(all_results),
        "tests": all_results,
        "overall_success": all(r["success_rate"] == "100.0%" for r in all_results),
        "max_concurrent_workers": max(test[0] for test in test_scenarios),
        "total_queries_executed": sum(r["total_queries"] for r in all_results),
        "total_test_duration": sum(r["total_duration_seconds"] for r in all_results)
    }

    # Print summary
    logger.info(f"\n{'='*60}")
    logger.info("LOAD TEST SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Test Scenarios: {len(all_results)}")
    logger.info(f"Total Queries: {summary['total_queries_executed']}")
    logger.info(f"Total Duration: {summary['total_test_duration']:.2f}s")
    logger.info(f"All Tests Passed: {'✅ YES' if summary['overall_success'] else '❌ NO'}")
    logger.info(f"Max Concurrent Workers: {summary['max_concurrent_workers']}")
    logger.info(f"{'='*60}\n")

    # Save results
    with open("CONNECTION_POOL_LOAD_TEST_RESULTS.json", "w") as f:
        json.dump(summary, f, indent=2)

    logger.info("✅ Results saved to: CONNECTION_POOL_LOAD_TEST_RESULTS.json")

    return summary

if __name__ == "__main__":
    main()
