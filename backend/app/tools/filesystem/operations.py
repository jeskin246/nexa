"""
NEXA Filesystem Tools — Search, read, create, write, copy, move, delete files.
"""

from __future__ import annotations

import glob
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import aiofiles
from loguru import logger

from app.security.permissions import PermissionLevel
from app.tools.base import Tool, ToolParameter, ToolResult


class FileSearchTool(Tool):
    @property
    def name(self) -> str:
        return "filesystem.search"

    @property
    def description(self) -> str:
        return (
            "Search for files on the filesystem. Can search by name pattern, "
            "extension, or content. Supports glob patterns."
        )

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="query", type="string",
                description="Search query — filename, pattern (e.g., '*.pdf'), or text to find",
            ),
            ToolParameter(
                name="path", type="string",
                description="Directory to search in",
                required=False,
            ),
            ToolParameter(
                name="file_type", type="string",
                description="File extension filter (e.g., '.pdf', '.java', '.py')",
                required=False,
            ),
            ToolParameter(
                name="max_results", type="integer",
                description="Maximum results to return",
                required=False, default=50,
            ),
            ToolParameter(
                name="recursive", type="boolean",
                description="Search subdirectories",
                required=False, default=True,
            ),
        ]

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.LOW

    async def execute(self, **params: Any) -> ToolResult:
        try:
            query = params.get("query", "*")
            search_path = params.get("path", str(Path.home()))
            file_type = params.get("file_type", "")
            max_results = params.get("max_results", 50)
            recursive = params.get("recursive", True)

            search_dir = Path(search_path)
            if not search_dir.exists():
                return ToolResult.fail(f"Directory not found: {search_path}")

            # Build glob pattern
            if file_type:
                if not file_type.startswith("."):
                    file_type = f".{file_type}"
                pattern = f"**/*{file_type}" if recursive else f"*{file_type}"
            elif "*" in query or "?" in query:
                pattern = f"**/{query}" if recursive else query
            else:
                pattern = f"**/*{query}*" if recursive else f"*{query}*"

            results = []
            try:
                for p in search_dir.glob(pattern):
                    if len(results) >= max_results:
                        break
                    try:
                        stat = p.stat()
                        results.append({
                            "path": str(p),
                            "name": p.name,
                            "size": stat.st_size,
                            "size_human": self._human_size(stat.st_size),
                            "modified": datetime.fromtimestamp(
                                stat.st_mtime
                            ).isoformat(),
                            "is_dir": p.is_dir(),
                        })
                    except (PermissionError, OSError):
                        continue
            except Exception as e:
                logger.warning(f"Search error in {search_path}: {e}")

            # Sort by modification time (newest first)
            results.sort(
                key=lambda r: r.get("modified", ""), reverse=True
            )

            return ToolResult.ok(
                data={
                    "files": results,
                    "count": len(results),
                    "search_path": str(search_dir),
                    "pattern": pattern,
                },
                message=f"Found {len(results)} files matching '{query}'",
            )
        except Exception as e:
            return ToolResult.fail(str(e))

    @staticmethod
    def _human_size(size: int) -> str:
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"


class FileReadTool(Tool):
    @property
    def name(self) -> str:
        return "filesystem.read"

    @property
    def description(self) -> str:
        return "Read the contents of a text file."

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="path", type="string",
                description="Path to the file to read",
            ),
            ToolParameter(
                name="max_lines", type="integer",
                description="Maximum number of lines to read",
                required=False, default=200,
            ),
        ]

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.LOW

    async def execute(self, **params: Any) -> ToolResult:
        try:
            file_path = Path(params.get("path", ""))
            max_lines = params.get("max_lines", 200)

            if not file_path.exists():
                return ToolResult.fail(f"File not found: {file_path}")
            if file_path.is_dir():
                return ToolResult.fail(f"Path is a directory: {file_path}")

            async with aiofiles.open(
                str(file_path), "r", encoding="utf-8", errors="replace"
            ) as f:
                lines = []
                async for line in f:
                    lines.append(line)
                    if len(lines) >= max_lines:
                        break

            content = "".join(lines)
            stat = file_path.stat()

            return ToolResult.ok(
                data={
                    "content": content,
                    "path": str(file_path),
                    "lines": len(lines),
                    "size": stat.st_size,
                    "truncated": len(lines) >= max_lines,
                },
                message=f"Read {len(lines)} lines from {file_path.name}",
            )
        except UnicodeDecodeError:
            return ToolResult.fail(
                f"Cannot read binary file: {file_path}"
            )
        except Exception as e:
            return ToolResult.fail(str(e))


class FileCreateTool(Tool):
    @property
    def name(self) -> str:
        return "filesystem.create"

    @property
    def description(self) -> str:
        return "Create a new file or directory."

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="path", type="string",
                description="Path for the new file or directory",
            ),
            ToolParameter(
                name="content", type="string",
                description="File content (omit for directories)",
                required=False,
            ),
            ToolParameter(
                name="is_directory", type="boolean",
                description="Create a directory instead of a file",
                required=False, default=False,
            ),
        ]

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.MEDIUM

    async def execute(self, **params: Any) -> ToolResult:
        try:
            target = Path(params.get("path", ""))
            content = params.get("content", "")
            is_dir = params.get("is_directory", False)

            if not target.parent.exists():
                target.parent.mkdir(parents=True, exist_ok=True)

            if is_dir:
                target.mkdir(parents=True, exist_ok=True)
                return ToolResult.ok(
                    data={"path": str(target)},
                    message=f"Created directory: {target}",
                )
            else:
                async with aiofiles.open(
                    str(target), "w", encoding="utf-8"
                ) as f:
                    await f.write(content)
                return ToolResult.ok(
                    data={"path": str(target), "size": len(content)},
                    message=f"Created file: {target}",
                )
        except Exception as e:
            return ToolResult.fail(str(e))


class FileWriteTool(Tool):
    @property
    def name(self) -> str:
        return "filesystem.write"

    @property
    def description(self) -> str:
        return "Write or append content to a file."

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="path", type="string",
                description="Path to the file",
            ),
            ToolParameter(
                name="content", type="string",
                description="Content to write",
            ),
            ToolParameter(
                name="append", type="boolean",
                description="Append to file instead of overwriting",
                required=False, default=False,
            ),
        ]

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.MEDIUM

    async def execute(self, **params: Any) -> ToolResult:
        try:
            path = Path(params.get("path", ""))
            content = params.get("content", "")
            append = params.get("append", False)

            mode = "a" if append else "w"
            async with aiofiles.open(str(path), mode, encoding="utf-8") as f:
                await f.write(content)

            action = "Appended to" if append else "Wrote to"
            return ToolResult.ok(
                data={"path": str(path), "size": len(content)},
                message=f"{action} {path.name}",
            )
        except Exception as e:
            return ToolResult.fail(str(e))


class FileCopyTool(Tool):
    @property
    def name(self) -> str:
        return "filesystem.copy"

    @property
    def description(self) -> str:
        return "Copy a file or directory to a new location."

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(name="source", type="string", description="Source path"),
            ToolParameter(name="destination", type="string", description="Destination path"),
        ]

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.MEDIUM

    async def execute(self, **params: Any) -> ToolResult:
        try:
            src = Path(params.get("source", ""))
            dst = Path(params.get("destination", ""))

            if not src.exists():
                return ToolResult.fail(f"Source not found: {src}")

            if src.is_dir():
                shutil.copytree(str(src), str(dst))
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src), str(dst))

            return ToolResult.ok(
                data={"source": str(src), "destination": str(dst)},
                message=f"Copied {src.name} to {dst}",
            )
        except Exception as e:
            return ToolResult.fail(str(e))


class FileMoveTool(Tool):
    @property
    def name(self) -> str:
        return "filesystem.move"

    @property
    def description(self) -> str:
        return "Move a file or directory to a new location."

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(name="source", type="string", description="Source path"),
            ToolParameter(name="destination", type="string", description="Destination path"),
        ]

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.MEDIUM

    async def execute(self, **params: Any) -> ToolResult:
        try:
            src = Path(params.get("source", ""))
            dst = Path(params.get("destination", ""))

            if not src.exists():
                return ToolResult.fail(f"Source not found: {src}")

            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))

            return ToolResult.ok(
                data={"source": str(src), "destination": str(dst)},
                message=f"Moved {src.name} to {dst}",
            )
        except Exception as e:
            return ToolResult.fail(str(e))


class FileDeleteTool(Tool):
    @property
    def name(self) -> str:
        return "filesystem.delete"

    @property
    def description(self) -> str:
        return "Delete a file or directory. This is a HIGH RISK operation."

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="path", type="string",
                description="Path to delete",
            ),
        ]

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.HIGH  # Always requires confirmation

    async def execute(self, **params: Any) -> ToolResult:
        try:
            target = Path(params.get("path", ""))

            if not target.exists():
                return ToolResult.fail(f"Path not found: {target}")

            if target.is_dir():
                shutil.rmtree(str(target))
                msg = f"Deleted directory: {target}"
            else:
                target.unlink()
                msg = f"Deleted file: {target}"

            logger.info(msg)
            return ToolResult.ok(message=msg)
        except Exception as e:
            return ToolResult.fail(str(e))


class FileRenameTool(Tool):
    @property
    def name(self) -> str:
        return "filesystem.rename"

    @property
    def description(self) -> str:
        return "Rename a file or directory."

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(name="path", type="string", description="Current file path"),
            ToolParameter(name="new_name", type="string", description="New name (just filename, not full path)"),
        ]

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.MEDIUM

    async def execute(self, **params: Any) -> ToolResult:
        try:
            target = Path(params.get("path", ""))
            new_name = params.get("new_name", "")

            if not target.exists():
                return ToolResult.fail(f"Path not found: {target}")
            if not new_name:
                return ToolResult.fail("New name not provided")

            new_path = target.parent / new_name
            target.rename(new_path)

            return ToolResult.ok(
                data={"old_path": str(target), "new_path": str(new_path)},
                message=f"Renamed {target.name} to {new_name}",
            )
        except Exception as e:
            return ToolResult.fail(str(e))


def get_tools() -> list[Tool]:
    return [
        FileSearchTool(),
        FileReadTool(),
        FileCreateTool(),
        FileWriteTool(),
        FileCopyTool(),
        FileMoveTool(),
        FileDeleteTool(),
        FileRenameTool(),
    ]
