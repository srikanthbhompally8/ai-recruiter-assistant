"""Celery tasks for async job processing."""

from .parse_job import parse_job_description_async

__all__ = ["parse_job_description_async"]
