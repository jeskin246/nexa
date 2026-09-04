"""
NEXA OS Tools — System information, processes, network.
"""

from __future__ import annotations

from typing import Any

import psutil
from loguru import logger

from app.security.permissions import PermissionLevel
from app.tools.base import Tool, ToolParameter, ToolResult


class SystemInfoTool(Tool):
    @property
    def name(self) -> str:
        return "os.system_info"

    @property
    def description(self) -> str:
        return (
            "Get system information including CPU usage, memory usage, "
            "disk usage, network stats, and battery status."
        )

    @property
    def parameters(self) -> list[ToolParameter]:
        return []

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.LOW

    async def execute(self, **params: Any) -> ToolResult:
        try:
            cpu_percent = psutil.cpu_percent(interval=0.5)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            net = psutil.net_io_counters()
            boot_time = psutil.boot_time()

            battery = None
            try:
                bat = psutil.sensors_battery()
                if bat:
                    battery = {
                        "percent": bat.percent,
                        "charging": bat.power_plugged,
                        "seconds_left": bat.secsleft if bat.secsleft > 0 else None,
                    }
            except Exception:
                pass

            data = {
                "cpu_percent": cpu_percent,
                "cpu_count": psutil.cpu_count(),
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "percent": memory.percent,
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "percent": round(disk.percent, 1),
                },
                "network": {
                    "bytes_sent": net.bytes_sent,
                    "bytes_recv": net.bytes_recv,
                },
                "battery": battery,
                "boot_time": boot_time,
                "process_count": len(psutil.pids()),
            }

            return ToolResult.ok(
                data=data,
                message=(
                    f"CPU: {cpu_percent}%, "
                    f"RAM: {memory.percent}%, "
                    f"Disk: {disk.percent}%"
                ),
            )
        except Exception as e:
            return ToolResult.fail(str(e))


class ProcessesTool(Tool):
    @property
    def name(self) -> str:
        return "os.processes"

    @property
    def description(self) -> str:
        return (
            "List running processes with details like name, PID, CPU usage, "
            "and memory usage. Can filter by name."
        )

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="filter_name", type="string",
                description="Optional process name filter (case-insensitive)",
                required=False,
            ),
            ToolParameter(
                name="limit", type="integer",
                description="Maximum number of processes to return",
                required=False, default=30,
            ),
            ToolParameter(
                name="sort_by", type="string",
                description="Sort by: name, cpu, memory, pid",
                required=False, default="memory",
                enum=["name", "cpu", "memory", "pid"],
            ),
        ]

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.LOW

    async def execute(self, **params: Any) -> ToolResult:
        try:
            filter_name = params.get("filter_name", "")
            limit = params.get("limit", 30)
            sort_by = params.get("sort_by", "memory")

            processes = []
            for proc in psutil.process_iter(
                ["pid", "name", "cpu_percent", "memory_percent", "status"]
            ):
                try:
                    info = proc.info
                    if filter_name and filter_name.lower() not in info["name"].lower():
                        continue
                    processes.append({
                        "pid": info["pid"],
                        "name": info["name"],
                        "cpu_percent": round(info.get("cpu_percent", 0) or 0, 1),
                        "memory_percent": round(info.get("memory_percent", 0) or 0, 1),
                        "status": info.get("status", "unknown"),
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Sort
            sort_keys = {
                "name": lambda p: p["name"].lower(),
                "cpu": lambda p: p["cpu_percent"],
                "memory": lambda p: p["memory_percent"],
                "pid": lambda p: p["pid"],
            }
            key_func = sort_keys.get(sort_by, sort_keys["memory"])
            reverse = sort_by in ("cpu", "memory")
            processes.sort(key=key_func, reverse=reverse)

            processes = processes[:limit]

            return ToolResult.ok(
                data={
                    "processes": processes,
                    "total_count": len(psutil.pids()),
                    "returned_count": len(processes),
                },
                message=f"Found {len(processes)} processes",
            )
        except Exception as e:
            return ToolResult.fail(str(e))


class NetworkInfoTool(Tool):
    @property
    def name(self) -> str:
        return "os.network"

    @property
    def description(self) -> str:
        return "Get network interface information and connection statistics."

    @property
    def parameters(self) -> list[ToolParameter]:
        return []

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.LOW

    async def execute(self, **params: Any) -> ToolResult:
        try:
            interfaces = {}
            addrs = psutil.net_if_addrs()
            stats = psutil.net_if_stats()

            for name, addr_list in addrs.items():
                iface_info = {"addresses": [], "is_up": False}
                for addr in addr_list:
                    iface_info["addresses"].append({
                        "family": str(addr.family),
                        "address": addr.address,
                    })
                if name in stats:
                    iface_info["is_up"] = stats[name].isup
                    iface_info["speed"] = stats[name].speed
                interfaces[name] = iface_info

            counters = psutil.net_io_counters()

            return ToolResult.ok(
                data={
                    "interfaces": interfaces,
                    "io_counters": {
                        "bytes_sent": counters.bytes_sent,
                        "bytes_recv": counters.bytes_recv,
                        "packets_sent": counters.packets_sent,
                        "packets_recv": counters.packets_recv,
                    },
                },
                message=f"Found {len(interfaces)} network interfaces",
            )
        except Exception as e:
            return ToolResult.fail(str(e))


def get_tools() -> list[Tool]:
    return [SystemInfoTool(), ProcessesTool(), NetworkInfoTool()]
