import sys
from pathlib import Path

# Add the repo root to the Python path so pipeline can be imported
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))
