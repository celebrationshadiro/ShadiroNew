"""Compatibility wrapper for legacy app.main imports.

Use backend.main:app as the only runtime entrypoint.
"""

from main import app

__all__ = ["app"]
