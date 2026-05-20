"""Tool registration and execution system."""

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    """Tool definition with schema and executor."""
    name: str
    schema: Dict[str, Any]
    executor: Callable
    description: str = ""
    is_handoff: bool = False
    target_agent: Optional[str] = None


# Global tool registry
_TOOL_REGISTRY: Dict[str, ToolDefinition] = {}


def register_tool(
    name: str,
    schema: Dict[str, Any],
    executor: Callable,
    description: str = "",
    is_handoff: bool = False,
    target_agent: Optional[str] = None,
) -> None:
    """Register a tool globally."""
    tool = ToolDefinition(
        name=name,
        schema=schema,
        executor=executor,
        description=description,
        is_handoff=is_handoff,
        target_agent=target_agent,
    )
    _TOOL_REGISTRY[name] = tool
    logger.info(f"✅ Registered tool: {name}")


def get_tool(name: str) -> Optional[ToolDefinition]:
    """Get a tool by name."""
    return _TOOL_REGISTRY.get(name)


def list_tools() -> Dict[str, ToolDefinition]:
    """List all registered tools."""
    return _TOOL_REGISTRY.copy()


async def execute_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a tool by name."""
    tool = get_tool(name)
    if not tool:
        return {"error": f"Tool '{name}' not found"}
    
    try:
        result = await tool.executor(arguments)
        return result
    except Exception as e:
        logger.error(f"❌ Tool execution failed: {name} - {e}")
        return {"error": str(e)}


def initialize_tools() -> None:
    """Initialize all tools (stub for now)."""
    # TODO: Load tools from modules
    logger.info("🔧 Tools initialized (placeholder)")
