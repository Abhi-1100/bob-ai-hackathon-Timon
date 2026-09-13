"""
Root entry point wrapper for Threat Intelligence Assistant backend.
Enables running `uvicorn main:app --reload` or `python main.py` directly from the workspace root.
"""

import sys
from pathlib import Path

# Add src and src/backend directories to sys.path
root_dir = Path(__file__).resolve().parent
src_dir = root_dir / "src"
backend_dir = src_dir / "backend"

for path in (backend_dir, src_dir, root_dir):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from backend.main import app  # noqa: E402, F401

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
