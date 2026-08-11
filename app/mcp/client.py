"""MCP Client Base and Protocol Handler."""
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger("gwc.mcp")


class BaseMCPClient:
    """Base client class for Model Context Protocol (MCP) integrations."""
    def __init__(self, server_url: Optional[str] = None):
        self.server_url = server_url
        self._available_tools: List[str] = []

    async def discover_tools(self) -> List[str]:
        """Discover tools exposed by the MCP server."""
        return self._available_tools

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific MCP tool."""
        raise NotImplementedError
