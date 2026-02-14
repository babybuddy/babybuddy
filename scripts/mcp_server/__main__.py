from __future__ import annotations

from fastmcp import FastMCP

from mcp_server.tools import register_all

mcp = FastMCP("Baby Buddy Dev")
register_all(mcp)
mcp.run()
