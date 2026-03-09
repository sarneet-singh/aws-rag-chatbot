import sys
from pathlib import Path

# Add project root to path so `from src.ingestion import ...` works
sys.path.insert(0, str(Path(__file__).parent))
