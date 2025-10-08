# dispatcher/config.py
"""
Configuration module for the dispatcher service.
"""
import os
import logging
from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse
from dotenv import load_dotenv

# Load .env for local dev; in Docker/prod you'll pass real env vars
load_dotenv()

_LOG = logging.getLogger(__name__)

def _coerce_log_level(value: str) -> int:
    value = (value or "INFO").upper()
    return getattr(logging, value, logging.INFO)

def _masked_url(url: str) -> str:
    try:
        p = urlparse(url)
        # Rebuild netloc without the password
        if p.password is not None:
            netloc = p.hostname or ""
            if p.username:
                netloc = f"{p.username}:***@{netloc}"
            if p.port:
                netloc = f"{netloc}:{p.port}"
            p = p._replace(netloc=netloc)
        return urlunparse(p)
    except Exception:
        return "scheme://***:***@host:port"

def _require(name: str, default: str | None = None) -> str:
    val = os.getenv(name, default)
    if val is None or val == "":
        raise ValueError(f"Environment variable {name} is required")
    return val

def _get_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except ValueError:
        raise ValueError(f"{name} must be a number")

def _get_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        raise ValueError(f"{name} must be an integer")

@dataclass(frozen=True)
class Config:
    # Core URLs
    redis_url: str
    mongo_uri: str

    # Logging
    log_level_name: str
    log_level: int

    # Redis keys / consumer
    stream_outgoing: str
    zset_scheduled: str
    hash_job_prefix: str
    consumer_group: str
    consumer_name: str

    # Timing
    scheduler_interval: float  # seconds

    @staticmethod
    def from_env() -> "Config":
        redis_url = _require("REDIS_URL")  # e.g. rediss://default:pass@host:port/0
        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            raise ValueError("MONGO_URI is required")

        # Validate Redis TLS when using Redis Cloud
        parsed = urlparse(redis_url)
        if (parsed.hostname or "").endswith(("redns.redis-cloud.com", "redis-cloud.com")) and parsed.scheme != "rediss":
            raise ValueError("REDIS_URL must use rediss:// (TLS) for Redis Cloud")

        log_level_name = os.getenv("LOG_LEVEL", "INFO")
        log_level = _coerce_log_level(log_level_name)

        cfg = Config(
            redis_url=redis_url,
            mongo_uri=mongo_uri,
            log_level_name=log_level_name,
            log_level=log_level,
            stream_outgoing=os.getenv("STREAM_OUTGOING", "stream:outgoing"),
            zset_scheduled=os.getenv("ZSET_SCHEDULED", "zset:scheduled"),
            hash_job_prefix=os.getenv("HASH_JOB_PREFIX", "hash:job:"),
            consumer_group=os.getenv("CONSUMER_GROUP", "dispatcher-group"),
            consumer_name=os.getenv("CONSUMER_NAME", "dispatcher-consumer"),
            scheduler_interval=_get_float("DISPATCHER_POLL_INTERVAL", 1.0),
        )

        # Apply logging level globally (optional; or do it in main)
        logging.getLogger().setLevel(cfg.log_level)
        _LOG.info("Configuration loaded | Redis=%s | Mongo=%s | Level=%s",
                  _masked_url(cfg.redis_url), cfg.mongo_uri, cfg.log_level_name)
        return cfg

    def job_hash_key(self, job_id: str) -> str:
        return f"{self.hash_job_prefix}{job_id}"

# Lazy singleton, avoids crashing on import if env is missing
_config_instance: Config | None = None

def get_config() -> Config:
    global _config_instance
    if _config_instance is None:
        _config_instance = Config.from_env()
    return _config_instance

# Export a config instance for convenience
config = get_config()