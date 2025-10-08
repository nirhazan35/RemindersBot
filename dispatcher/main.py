import asyncio
import logging
import signal
import sys
from typing import Set, Optional

from config import config
from scheduler import scheduler
from stream_reader import stream_reader

# Configure logging early
logging.basicConfig(
    level=config.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)
logging.getLogger().setLevel(config.log_level)


class DispatcherService:
    """Main dispatcher service that orchestrates scheduler and stream reader."""

    def __init__(self) -> None:
        self._running: bool = False
        self._tasks: Set[asyncio.Task] = set()
        self._stop_lock = asyncio.Lock()
        self._connected = False

    async def start(self) -> None:
        """Start the dispatcher service."""
        logger.info("Starting Dispatcher Service")
        try:
            # Connect components
            await scheduler.connect()
            try:
                await stream_reader.connect()
            except Exception:
                # Roll back scheduler if stream_reader failed
                await scheduler.disconnect()
                raise

            self._connected = True
            self._running = True

            # Create tasks
            scheduler_task = asyncio.create_task(
                scheduler.run_scheduler_loop(), name="scheduler_loop"
            )
            reader_task = asyncio.create_task(
                stream_reader.run_reader_loop(), name="stream_reader_loop"
            )

            # Log unhandled exceptions from tasks
            for t in (scheduler_task, reader_task):
                t.add_done_callback(self._log_task_exception)
                self._tasks.add(t)

            logger.info("Dispatcher service started successfully")

            # Wait until tasks complete (usually on cancellation)
            await asyncio.gather(*self._tasks)

        except asyncio.CancelledError:
            # Normal during shutdown
            raise
        except Exception as e:
            logger.exception("Error starting dispatcher service: %s", e)
            raise

    def _log_task_exception(self, task: asyncio.Task) -> None:
        if task.cancelled():
            return
        exc = task.exception()
        if exc:
            logger.error("Task %s failed: %s", task.get_name(), exc, exc_info=exc)

    async def stop(self) -> None:
        """Stop the dispatcher service (idempotent)."""
        async with self._stop_lock:
            if not self._running:
                return

            logger.info("Stopping Dispatcher Service")
            self._running = False

            # Signal components to stop their loops
            try:
                scheduler.stop_scheduler()
            except Exception as e:
                logger.warning("scheduler.stop_scheduler() raised: %s", e)

            try:
                stream_reader.stop_reader()
            except Exception as e:
                logger.warning("stream_reader.stop_reader() raised: %s", e)

            # Cancel tasks
            for task in list(self._tasks):
                if not task.done():
                    task.cancel()

            if self._tasks:
                # Wait for tasks to cancel, with a timeout
                done, pending = await asyncio.wait(self._tasks, timeout=5)
                for p in pending:
                    logger.warning("Task %s did not finish on time; cancelling again.", p.get_name())
                    p.cancel()

            # Disconnect after tasks stop
            if self._connected:
                try:
                    await stream_reader.disconnect()
                except Exception as e:
                    logger.warning("stream_reader.disconnect() raised: %s", e)
                try:
                    await scheduler.disconnect()
                except Exception as e:
                    logger.warning("scheduler.disconnect() raised: %s", e)
                self._connected = False

            self._tasks.clear()
            logger.info("Dispatcher service stopped")

    def setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        loop = asyncio.get_running_loop()

        def _request_stop() -> None:
            loop.create_task(self.stop())

        # Prefer asyncio loop signal handlers on Unix
        try:
            loop.add_signal_handler(signal.SIGINT, _request_stop)
            loop.add_signal_handler(signal.SIGTERM, _request_stop)
            logger.debug("Using loop.add_signal_handler for SIGINT/SIGTERM")
        except NotImplementedError:
            # Fallback (e.g., on Windows)
            def _sync_handler(signum, frame):
                loop.call_soon_threadsafe(_request_stop)
            signal.signal(signal.SIGINT, _sync_handler)
            signal.signal(signal.SIGTERM, _sync_handler)
            logger.debug("Using signal.signal fallback for SIGINT/SIGTERM")


async def main() -> int:
    """Main function to run the dispatcher service."""
    dispatcher = DispatcherService()
    try:
        dispatcher.setup_signal_handlers()
        await dispatcher.start()
        return 0
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt")
        return 0
    except asyncio.CancelledError:
        return 0
    except Exception as e:
        logger.error("Unhandled error in main: %s", e, exc_info=e)
        return 1
    finally:
        # Ensure cleanup even if start() raised
        try:
            await dispatcher.stop()
        except Exception as e:
            logger.warning("Error while stopping dispatcher: %s", e)


if __name__ == "__main__":
    # Guard against nested event loops
    try:
        exit_code = asyncio.run(main())
    except Exception as e:
        logger.error("Fatal error before loop: %s", e, exc_info=e)
        exit_code = 1
    sys.exit(exit_code)