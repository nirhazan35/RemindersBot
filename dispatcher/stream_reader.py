"""
Stream reader module for consuming messages from Redis streams.
"""
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Tuple

import redis.asyncio as redis
from redis.exceptions import ResponseError  # correct exception class
from config import config

logger = logging.getLogger(__name__)


class StreamReader:
    """Handles reading messages from Redis streams using consumer groups."""

    def __init__(self) -> None:
        self.redis_client: Optional[redis.Redis] = None
        self.running: bool = False

    # ----------------------
    # Lifecycle
    # ----------------------
    async def connect(self) -> None:
        """Connect to Redis and setup consumer group."""
        try:
            self.redis_client = redis.from_url(
                config.redis_url,
                decode_responses=True,
                health_check_interval=30,
                socket_connect_timeout=5.0,
                socket_timeout=5.0,
            )
            # Test connection
            pong = await self.redis_client.ping()
            if pong is True:
                logger.info("StreamReader connected to Redis successfully")
            else:
                logger.warning("Redis PING returned non-True: %s", pong)

            # Create consumer group if it doesn't exist
            await self._ensure_consumer_group()

        except Exception as e:
            logger.error("Failed to connect to Redis: %s", e)
            raise

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis_client:
            try:
                await self.redis_client.close()
                await self.redis_client.connection_pool.disconnect()
            finally:
                logger.info("StreamReader disconnected from Redis")

    # ----------------------
    # Group management
    # ----------------------
    async def _ensure_consumer_group(self) -> None:
        """Ensure the consumer group exists for the stream."""
        if not self.redis_client:
            raise RuntimeError("Redis client not connected")

        try:
            # Create the group at the END of the stream so we only consume new messages.
            await self.redis_client.xgroup_create(
                config.stream_outgoing,
                config.consumer_group,
                id="$",
                mkstream=True,
            )
            logger.info(
                "Created consumer group '%s' for stream '%s'",
                config.consumer_group,
                config.stream_outgoing,
            )
        except ResponseError as e:
            # Group already exists
            if "BUSYGROUP" in str(e):
                logger.debug(
                    "Consumer group '%s' already exists for stream '%s'",
                    config.consumer_group,
                    config.stream_outgoing,
                )
            else:
                logger.error("Error creating consumer group: %s", e)
                raise

    # ----------------------
    # Reading / processing
    # ----------------------
    async def read_new_messages(
        self, count: int = 25, block_ms: int = 2000
    ) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Read new messages from the stream using XREADGROUP.

        Args:
            count: Maximum number of messages to read.
            block_ms: Block time in milliseconds (0 for non-blocking).

        Returns:
            List of tuples (message_id, message_data)
        """
        if not self.redis_client:
            raise RuntimeError("Redis client not connected")

        try:
            response = await self.redis_client.xreadgroup(
                config.consumer_group,
                config.consumer_name,
                {config.stream_outgoing: ">"},
                count=count,
                block=block_ms,
            )

            messages: List[Tuple[str, Dict[str, Any]]] = []
            if response:
                for _stream_name, stream_messages in response:
                    for message_id, fields in stream_messages:
                        messages.append((message_id, fields))

            return messages

        except Exception as e:
            logger.error("Error reading from stream: %s", e)
            return []

    async def acknowledge_message(self, message_id: str) -> bool:
        """Acknowledge a message as processed."""
        if not self.redis_client:
            raise RuntimeError("Redis client not connected")

        try:
            result = await self.redis_client.xack(
                config.stream_outgoing, config.consumer_group, message_id
            )
            return result > 0
        except Exception as e:
            logger.error("Error acknowledging message %s: %s", message_id, e)
            return False

    def _parse_job(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a stream message into a job dict.
        Supports two formats:
        1) {"job": "<json-string>"}  (recommended)
        2) flat hash (legacy)
        """
        if "job" in message_data:
            try:
                return json.loads(message_data["job"])
            except Exception:
                logger.warning("Failed to decode job JSON; returning raw fields")
                return message_data
        return message_data

    async def process_message(self, message_id: str, message_data: Dict[str, Any]) -> bool:
        """
        Process a single message. For now, we just log/print the parsed job JSON.
        Replace this with rate-limit, cooldown, send_via_baileys, and message_log writes.
        """
        try:
            job = self._parse_job(message_data)
            logger.info("Processing message %s (job_id=%s, kind=%s)",
                        message_id, job.get("job_id"), job.get("kind"))
            # Developer-friendly print (kept for parity with previous behavior)
            print("Job JSON:", json.dumps(job, indent=2, ensure_ascii=False))

            # Acknowledge the message only after successful handling
            await self.acknowledge_message(message_id)
            return True

        except Exception as e:
            logger.error("Error processing message %s: %s", message_id, e)
            # Intentionally NOT ack-ing on error so it can be retried or claimed from PEL.
            return False

    # ----------------------
    # Loop control
    # ----------------------
    async def run_reader_loop(self) -> None:
        """Run the stream reader loop that continuously reads and processes messages."""
        self.running = True
        logger.info("Starting stream reader loop (group=%s, consumer=%s)",
                    config.consumer_group, config.consumer_name)

        while self.running:
            try:
                messages = await self.read_new_messages(count=25, block_ms=2000)

                for message_id, message_data in messages:
                    ok = await self.process_message(message_id, message_data)
                    if not ok:
                        # Small backoff on failures to avoid tight error loops
                        await asyncio.sleep(0.5)

                if not messages:
                    # Tiny delay to avoid busy spinning when idle
                    await asyncio.sleep(0.1)

            except Exception as e:
                logger.error("Error in stream reader loop: %s", e)
                await asyncio.sleep(1.0)  # Longer delay on error

    def stop_reader(self) -> None:
        """Stop the stream reader loop."""
        self.running = False
        logger.info("Stream reader loop stop requested")


# Global stream reader instance
stream_reader = StreamReader()
