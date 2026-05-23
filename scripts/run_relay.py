from __future__ import annotations

import uvicorn
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


if __name__ == "__main__":
    uvicorn.run("apps.relay.main:app", host="127.0.0.1", port=8001, reload=False)
