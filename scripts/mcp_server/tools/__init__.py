from __future__ import annotations

import importlib
import pkgutil
from types import ModuleType

from fastmcp import FastMCP


def register_all(mcp: FastMCP) -> None:
    """Discover tool submodules and call register(mcp) on each."""
    prefix = __name__ + "."
    for _importer, modname, _ispkg in pkgutil.iter_modules(__path__, prefix):  # type: ignore[attr-defined]
        mod: ModuleType = importlib.import_module(modname)
        register = getattr(mod, "register", None)
        if callable(register):
            register(mcp)
