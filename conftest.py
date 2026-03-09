import sys
from pathlib import Path

import pytest

# Add project root to path so `from src.ingestion import ...` works
sys.path.insert(0, str(Path(__file__).parent))


@pytest.fixture(autouse=True)
def clear_ssm_cache():
    from src.utils.ssm import _clear_cache
    _clear_cache()
    yield
    _clear_cache()
