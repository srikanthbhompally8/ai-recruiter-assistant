"""
Performance Measurement & Tracking Framework
Tracks metrics before/after optimization for comparison
"""

import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class QueryMetric:
    """Individual query metric"""

    query_id: str
    duration_ms: float
    timestamp: str
    endpoint: str
    status: str = "success"
    error: Optional[str] = None


@dataclass
class PerformanceSnapshot:
    """Snapshot of performance metrics at a point in time"""

    timestamp: str
    total_queries: int
    avg_query_time_ms: float
    p95_query_time_ms: float
    p99_query_time_ms: float
    min_query_time_ms: float
    max_query_time_ms: float
    queries_per_second: float
    error_count: int
    error_rate: float


class PerformanceTracker:
    """Tracks performance metrics for before/after comparison"""

    def __init__(self, name: str = "default"):
        self.name = name
        self.queries: List[QueryMetric] = []
        self.start_time = time.time()
        self.endpoint_stats: dict = defaultdict(lambda: {"count": 0, "total_time": 0})

    def record_query(
        self,
        query_id: str,
        duration_ms: float,
        endpoint: str,
        status: str = "success",
        error: Optional[str] = None,
    ):
        """Record a single query metric"""
        metric = QueryMetric(
            query_id=query_id,
            duration_ms=duration_ms,
            timestamp=datetime.now().isoformat(),
            endpoint=endpoint,
            status=status,
            error=error,
        )
        self.queries.append(metric)

        # Update endpoint stats
        self.endpoint_stats[endpoint]["count"] += 1
        self.endpoint_stats[endpoint]["total_time"] += duration_ms

        logger.debug(f"Recorded: {query_id} - {duration_ms}ms - {endpoint}")

    def get_statistics(self) -> PerformanceSnapshot:
        """Calculate statistics from recorded metrics"""
        if not self.queries:
            return PerformanceSnapshot(
                timestamp=datetime.now().isoformat(),
                total_queries=0,
                avg_query_time_ms=0,
                p95_query_time_ms=0,
                p99_query_time_ms=0,
                min_query_time_ms=0,
                max_query_time_ms=0,
                queries_per_second=0,
                error_count=0,
                error_rate=0,
            )

        durations = [q.duration_ms for q in self.queries if q.status == "success"]
        errors = [q for q in self.queries if q.status != "success"]

        if not durations:
            durations = [0]

        # Sort for percentile calculation
        sorted_durations = sorted(durations)
        total_queries = len(self.queries)
        error_count = len(errors)

        # Calculate percentiles
        def percentile(data, p):
            if not data:
                return 0
            idx = int(len(data) * p / 100)
            return data[min(idx, len(data) - 1)]

        # Calculate throughput
        uptime_seconds = time.time() - self.start_time
        qps = total_queries / uptime_seconds if uptime_seconds > 0 else 0

        return PerformanceSnapshot(
            timestamp=datetime.now().isoformat(),
            total_queries=total_queries,
            avg_query_time_ms=round(sum(durations) / len(durations), 2),
            p95_query_time_ms=round(percentile(sorted_durations, 95), 2),
            p99_query_time_ms=round(percentile(sorted_durations, 99), 2),
            min_query_time_ms=round(min(durations), 2),
            max_query_time_ms=round(max(durations), 2),
            queries_per_second=round(qps, 2),
            error_count=error_count,
            error_rate=round(
                (error_count / total_queries * 100) if total_queries > 0 else 0, 2
            ),
        )

    def get_endpoint_metrics(self) -> Dict[str, Dict[str, float]]:
        """Get metrics broken down by endpoint"""
        metrics = {}
        for endpoint, stats in self.endpoint_stats.items():
            count = stats["count"]
            total_time = stats["total_time"]
            avg_time = total_time / count if count > 0 else 0

            metrics[endpoint] = {
                "query_count": count,
                "total_time_ms": round(total_time, 2),
                "avg_time_ms": round(avg_time, 2),
                "queries_per_second": round(count / (time.time() - self.start_time), 2),
            }

        return metrics

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        stats = self.get_statistics()
        endpoint_metrics = self.get_endpoint_metrics()

        return {
            "report_name": f"Performance Report: {self.name}",
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": round(time.time() - self.start_time, 2),
            "summary": asdict(stats),
            "endpoint_metrics": endpoint_metrics,
            "total_metrics_recorded": len(self.queries),
        }

    def reset(self):
        """Reset all metrics"""
        self.queries = []
        self.start_time = time.time()
        self.endpoint_stats = defaultdict(lambda: {"count": 0, "total_time": 0})
        logger.info(f"Performance tracker '{self.name}' reset")


class ComparisonAnalyzer:
    """Analyzes before/after performance comparison"""

    @staticmethod
    def compare_snapshots(
        before: PerformanceSnapshot, after: PerformanceSnapshot
    ) -> Dict[str, Any]:
        """Compare two performance snapshots"""

        def calculate_improvement(before_val: float, after_val: float) -> float:
            """Calculate improvement percentage (positive = improvement)"""
            if before_val == 0:
                return 0
            return round(((before_val - after_val) / before_val) * 100, 1)

        return {
            "comparison": {
                "avg_query_time": {
                    "before_ms": before.avg_query_time_ms,
                    "after_ms": after.avg_query_time_ms,
                    "improvement_percent": calculate_improvement(
                        before.avg_query_time_ms, after.avg_query_time_ms
                    ),
                },
                "p95_query_time": {
                    "before_ms": before.p95_query_time_ms,
                    "after_ms": after.p95_query_time_ms,
                    "improvement_percent": calculate_improvement(
                        before.p95_query_time_ms, after.p95_query_time_ms
                    ),
                },
                "p99_query_time": {
                    "before_ms": before.p99_query_time_ms,
                    "after_ms": after.p99_query_time_ms,
                    "improvement_percent": calculate_improvement(
                        before.p99_query_time_ms, after.p99_query_time_ms
                    ),
                },
                "throughput": {
                    "before_qps": before.queries_per_second,
                    "after_qps": after.queries_per_second,
                    "improvement_percent": calculate_improvement(
                        before.queries_per_second, after.queries_per_second
                    )
                    * -1,  # Inverse for throughput (more is better)
                },
                "error_rate": {
                    "before_percent": before.error_rate,
                    "after_percent": after.error_rate,
                    "improvement_percent": calculate_improvement(
                        before.error_rate, after.error_rate
                    ),
                },
            },
            "summary": {
                "total_before": before.total_queries,
                "total_after": after.total_queries,
                "query_time_reduction": f"{calculate_improvement(before.avg_query_time_ms, after.avg_query_time_ms):.1f}%",
                "throughput_improvement": f"{abs(calculate_improvement(before.queries_per_second, after.queries_per_second)) * -1:.1f}%",
                "error_rate_reduction": f"{calculate_improvement(before.error_rate, after.error_rate):.1f}%",
            },
        }

    @staticmethod
    def generate_comparison_report(
        name: str, before: PerformanceSnapshot, after: PerformanceSnapshot
    ) -> Dict[str, Any]:
        """Generate full comparison report"""
        comparison = ComparisonAnalyzer.compare_snapshots(before, after)

        return {
            "report_name": f"Performance Comparison: {name}",
            "timestamp": datetime.now().isoformat(),
            "before_snapshot": asdict(before),
            "after_snapshot": asdict(after),
            "analysis": comparison,
        }


# Global tracker instances
_trackers = {}


def get_tracker(name: str = "default") -> PerformanceTracker:
    """Get or create a tracker by name"""
    if name not in _trackers:
        _trackers[name] = PerformanceTracker(name)
    return _trackers[name]


def reset_tracker(name: str = "default"):
    """Reset a tracker"""
    if name in _trackers:
        _trackers[name].reset()


def get_all_reports() -> Dict[str, Dict[str, Any]]:
    """Get reports from all trackers"""
    return {name: tracker.generate_report() for name, tracker in _trackers.items()}
