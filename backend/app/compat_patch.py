"""Python 3.14 + SQLAlchemy 2.0 compatibility patch.

CRITICAL: This module MUST be imported before any SQLAlchemy models.
It patches SQLAlchemy's make_union_type function to work with Python 3.14's
changed typing.Union behavior.

Issue: Python 3.14 changed Union's __getitem__ behavior, causing SQLAlchemy
to crash when processing Optional[] types with: 
TypeError: descriptor '__getitem__' requires a 'typing.Union' object but received a 'tuple'

This patch wraps the problematic function to handle Python 3.14 correctly.
"""

import sys
from typing import Union, Any

# Only apply patch for Python 3.14+
if sys.version_info >= (3, 14):
    try:
        from sqlalchemy.util import typing as sqla_typing
        
        # Store original function
        _original_make_union_type = sqla_typing.make_union_type
        
        def _patched_make_union_type(*types: Any) -> Any:
            """Patched version that handles Python 3.14's Union behavior."""
            if not types:
                return type(None)
            
            if len(types) == 1:
                return types[0]
            
            # Python 3.14 fix: Use Union directly with unpacked args
            # instead of Union.__getitem__(tuple)
            try:
                from typing import _UnionGenericAlias  # type: ignore
                return _UnionGenericAlias(Union, types)
            except (ImportError, AttributeError):
                # Fallback to original behavior
                return Union[types]  # type: ignore
        
        # Apply patch
        sqla_typing.make_union_type = _patched_make_union_type
        
        print("✓ Applied SQLAlchemy Python 3.14 compatibility patch")
        
    except ImportError:
        # SQLAlchemy not installed or different version
        pass
