"""
NEXA Tool System Tests.
"""

import pytest
from app.security.permissions import PermissionLevel
from app.tools.base import ToolResult
from app.tools.registry import ToolRegistry, discover_and_register_tools


@pytest.fixture
def registry():
    reg = ToolRegistry()
    discover_and_register_tools(reg)
    return reg


def test_tool_discovery(registry):
    """Test that all 34+ built-in tools are registered."""
    assert registry.count >= 30
    assert registry.has("screen.capture")
    assert registry.has("mouse.move")
    assert registry.has("keyboard.type")
    assert registry.has("clipboard.read")
    assert registry.has("os.system_info")
    assert registry.has("app.launch")
    assert registry.has("filesystem.search")
    assert registry.has("browser.open")


def test_tool_llm_schema(registry):
    """Test LLM schema generation for tools."""
    schemas = registry.get_llm_tools()
    assert len(schemas) == registry.count
    first = schemas[0]
    assert "type" in first
    assert first["type"] == "function"
    assert "name" in first["function"]
    assert "description" in first["function"]
    assert "parameters" in first["function"]


@pytest.mark.asyncio
async def test_system_info_tool(registry):
    """Test system info tool execution."""
    tool = registry.get("os.system_info")
    assert tool is not None
    result = await tool.execute()
    assert result.success is True
    assert "cpu_percent" in result.data
    assert "memory" in result.data
    assert "disk" in result.data


@pytest.mark.asyncio
async def test_filesystem_search_tool(registry, tmp_path):
    """Test filesystem search tool."""
    # Create test files
    (tmp_path / "test1.txt").write_text("hello world")
    (tmp_path / "test2.pdf").write_text("fake pdf")

    tool = registry.get("filesystem.search")
    result = await tool.execute(path=str(tmp_path), query="*.txt")

    assert result.success is True
    files = result.data.get("files", [])
    assert len(files) == 1
    assert files[0]["name"] == "test1.txt"


def test_android_send_whatsapp_tool_registration(registry):
    """Test that android.send_whatsapp tool is discovered and registered."""
    assert registry.has("android.send_whatsapp")
    tool = registry.get("android.send_whatsapp")
    assert tool is not None
    assert tool.name == "android.send_whatsapp"
    assert len(tool.parameters) >= 3

