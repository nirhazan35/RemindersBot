
"""
Scheduler module for moving due jobs from zset:scheduled to stream:outgoing.
"""

import asyncio
import time
import json
import logging
from typing import List, Tuple, Optional

import redis.asyncio as redis
from config import config

logger = logging.getLogger(__name__)


class JobScheduler:
    """Handles moving due jobs from scheduled zset to outgoing stream."""

    def __init__(self) -> None:
        self.redis_client: Optional[redis.Redis] = None
        self.running: bool = False

    # ----------------------
    # Lifecycle
    # ----------------------
    async def connect(self) -> None:
        """Connect to Redis (TLS if rediss://) and verify connectivity."""
        try:
            self.redis_client = redis.from_url(
                config.redis_url,
                decode_responses=True,
                health_check_interval=30,
                socket_connect_timeout=5.0,
                socket_timeout=5.0,
            )
            # Health check
            pong = await self.redis_client.ping()
            if pong is True:
                logger.info("Connected to Redis successfully")
            else:
                logger.warning("Redis PING returned non-True: %s", pong)
        except Exception as e:
            logger.error("Failed to connect to Redis: %s", e)
            raise

    async def disconnect(self) -> None:
        """Disconnect from Redis and close the pool."""
        if self.redis_client:
            try:
                await self.redis_client.close()
                await self.redis_client.connection_pool.disconnect()
            finally:
                logger.info("Disconnected from Redis")

    # ----------------------
    # Core ops
    # ----------------------
    async def get_due_jobs(self, current_time: int, limit: int = 200) -> List[Tuple[str, float]]:
        """
        Fetch up to `limit` jobs due for processing (score <= current_time) from the zset.
        Returns a list of (job_id, score) tuples.
        """
        if not self.redis_client:
            raise RuntimeError("Redis client not connected")
        try:
            return await self.redis_client.zrangebyscore(
                config.zset_scheduled,
                min="-inf",
                max=current_time,
                start=0,
                num=limit,
                withscores=True,
            )
        except Exception as e:
            logger.error("Error getting due jobs: %s", e)
            return []

    async def move_job_to_stream(self, job_id: str, score: float) -> bool:
        """
        Atomically move a single job to the outgoing stream and remove it from the zset.
        Expects job payload to be stored in a hash at key derived from config.job_hash_key(job_id).
        The stream message is a single field 'job' with a JSON payload.
        """
        if not self.redis_client:
            raise RuntimeError("Redis client not connected")
        try:
            job_hash_key = config.job_hash_key(job_id)
            job_data = await self.redis_client.hgetall(job_hash_key)
            if not job_data:
                # No data associated with this job; clean up the zset entry.
                logger.warning("Job data not found for job_id=%s; cleaning zset entry", job_id)
                await self.redis_client.zrem(config.zset_scheduled, job_id)
                return False

            payload = {
                "job": json.dumps(
                    {
                        **job_data,
                        "job_id": job_id,
                        "scheduled_time": int(score),
                        "processed_time": int(time.time()),
                    }
                )
            }

            async with self.redis_client.pipeline(transaction=True) as pipe:
                await pipe.xadd(config.stream_outgoing, payload)
                await pipe.zrem(config.zset_scheduled, job_id)
                await pipe.execute()

            logger.debug("Moved job %s → %s", job_id, config.stream_outgoing)
            return True

        except Exception as e:
            logger.error("Error moving job %s to stream: %s", job_id, e)
            return False

    async def process_due_jobs(self) -> int:
        """
        Process due jobs in small batches to avoid long blocking operations.
        Returns the total number of jobs moved in this tick.
        """
        if not self.redis_client:
            raise RuntimeError("Redis client not connected")

        total_processed = 0
        current_time = int(time.time())

        while True:
            batch = await self.get_due_jobs(current_time, limit=200)
            if not batch:
                break

            logger.debug("Processing %d due jobs", len(batch))
            for job_id, score in batch:
                try:
                    if await self.move_job_to_stream(job_id, score):
                        total_processed += 1
                except Exception as e:
                    logger.error("Failed to process job %s: %s", job_id, e)

            # Yield control between batches
            await asyncio.sleep(0)

        if total_processed:
            logger.info("Processed %d due jobs", total_processed)
        return total_processed

    # ----------------------
    # Loop control
    # ----------------------
    async def run_scheduler_loop(self) -> None:
        """Run the scheduler loop that processes due jobs every configured interval."""
        self.running = True
        logger.info("Starting scheduler loop (interval=%ss)", config.scheduler_interval)

        while self.running:
            try:
                await self.process_due_jobs()
            except Exception as e:
                logger.error("Error in scheduler loop: %s", e)
            finally:
                await asyncio.sleep(config.scheduler_interval)

    def stop_scheduler(self) -> None:
        """Signal the loop to stop."""
        self.running = False
        logger.info("Scheduler loop stop requested")


# Global scheduler instance
scheduler = JobScheduler()
