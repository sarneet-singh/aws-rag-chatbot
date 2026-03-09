import time

import boto3

_cache: dict[str, tuple[str, float]] = {}
_TTL = 300  # 5 minutes


def get_secret(path: str) -> str:
    """Fetch a SecureString from SSM Parameter Store with 5-minute TTL caching."""
    entry = _cache.get(path)
    if entry is not None:
        value, fetched_at = entry
        if time.time() - fetched_at < _TTL:
            return value
    ssm = boto3.client("ssm")
    value = ssm.get_parameter(Name=path, WithDecryption=True)["Parameter"]["Value"]
    _cache[path] = (value, time.time())
    return value


def _clear_cache() -> None:
    _cache.clear()
