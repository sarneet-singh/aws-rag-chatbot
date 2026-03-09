import boto3

_cache: dict[str, str] = {}


def get_secret(path: str) -> str:
    """Fetch a SecureString from SSM Parameter Store with in-process caching."""
    if path not in _cache:
        ssm = boto3.client("ssm")
        _cache[path] = ssm.get_parameter(Name=path, WithDecryption=True)["Parameter"]["Value"]
    return _cache[path]


def _clear_cache() -> None:
    _cache.clear()
