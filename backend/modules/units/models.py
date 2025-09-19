"""
Units Module - Models shim

To consolidate architecture, `UnitModel` now lives in `modules.content.models`.
This file re-exports `UnitModel` for backward compatibility during the transition.
"""

from modules.content.models import UnitModel  # noqa: F401

__all__ = ["UnitModel"]
