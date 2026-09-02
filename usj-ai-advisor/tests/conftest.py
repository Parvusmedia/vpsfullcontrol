import os
import sys
from pathlib import Path

os.environ.setdefault("AI_MODE", "mock")
os.environ["USJ_DATA_DIR"] = str(Path("/tmp/usj-ai-advisor-test-data"))
Path(os.environ["USJ_DATA_DIR"]).mkdir(parents=True, exist_ok=True)

BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND))
