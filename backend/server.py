"""Compatibility module.

Runtime entrypoint has been consolidated into backend/main.py.
"""

from main import app

__all__ = ["app"]
