"""
NEXA OS Tools — Application management.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

from loguru import logger

from app.security.permissions import PermissionLevel
from app.tools.base import Tool, ToolParameter, ToolResult


def find_installed_app(app_name: str) -> str | None:
    """
    Dynamically discover any application installed on Windows by searching:
    1. Registry App Paths (HKLM & HKCU)
    2. Start Menu Shortcuts (.lnk files in ProgramData & AppData)
    3. Windows App Execution Aliases
    4. Program Files & LocalAppData executables
    """
    app_clean = app_name.lower().strip()
    
    # 1. Registry App Paths
    try:
        import winreg
        for root_key in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            try:
                sub_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"
                with winreg.OpenKey(root_key, sub_path) as key:
                    num_subkeys = winreg.QueryInfoKey(key)[0]
                    for i in range(num_subkeys):
                        sk_name = winreg.EnumKey(key, i)
                        if app_clean in sk_name.lower():
                            with winreg.OpenKey(key, sk_name) as sk:
                                path_val, _ = winreg.QueryValueEx(sk, "")
                                if path_val and os.path.exists(path_val):
                                    return path_val
            except Exception:
                pass
    except Exception:
        pass

    # 2. Start Menu Shortcuts (.lnk files)
    start_menu_dirs = [
        Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData")) / r"Microsoft\Windows\Start Menu\Programs",
        Path.home() / r"AppData\Roaming\Microsoft\Windows\Start Menu\Programs",
    ]
    for sm_dir in start_menu_dirs:
        if sm_dir.exists():
            for lnk in sm_dir.rglob("*.lnk"):
                if app_clean in lnk.stem.lower():
                    return str(lnk)

    # 3. Windows Apps / Execution Aliases
    win_apps = Path.home() / r"AppData\Local\Microsoft\WindowsApps"
    if win_apps.exists():
        for exe in win_apps.glob("*.exe"):
            if app_clean in exe.stem.lower():
                return str(exe)

    # 4. Program Files & LocalAppData
    program_dirs = [
        Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")),
        Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")),
        Path.home() / r"AppData\Local\Programs",
    ]
    for p_dir in program_dirs:
        if p_dir.exists():
            for exe in p_dir.rglob("*.exe"):
                if app_clean in exe.stem.lower():
                    if not any(bad in exe.name.lower() for bad in ("unins", "setup", "helper", "update", "crash", "reporter")):
                        return str(exe)

    return None


def get_all_installed_apps() -> list[dict[str, str]]:
    """Scan and list all installed applications on Windows."""
    discovered: dict[str, str] = {}
    
    start_menu_dirs = [
        Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData")) / r"Microsoft\Windows\Start Menu\Programs",
        Path.home() / r"AppData\Roaming\Microsoft\Windows\Start Menu\Programs",
    ]
    for sm_dir in start_menu_dirs:
        if sm_dir.exists():
            for lnk in sm_dir.rglob("*.lnk"):
                name = lnk.stem
                if name and not any(bad in name.lower() for bad in ("uninstall", "help", "documentation", "readme", "website")):
                    discovered[name] = str(lnk)
                    
    return [{"name": k, "path": v} for k, v in sorted(discovered.items(), key=lambda x: x[0].lower())]


class AppLaunchTool(Tool):
    @property
    def name(self) -> str:
        return "app.launch"

    @property
    def description(self) -> str:
        return (
            "Launch any application by name or path. Supports all installed Windows "
            "applications, desktop shortcuts, and newly downloaded apps."
        )

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="name", type="string",
                description=(
                    "Application name (e.g., 'chrome', 'vscode', 'photoshop', 'zoom', 'vlc') "
                    "or executable / shortcut path"
                ),
            ),
            ToolParameter(
                name="args", type="string",
                description="Optional command-line arguments",
                required=False,
            ),
        ]

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.LOW

    async def execute(self, **params: Any) -> ToolResult:
        try:
            name = params.get("name", "")
            args = params.get("args", "")
            
            if not name:
                return ToolResult.fail("No application name provided")

            # Map common app names to executables
            app_map = {
                "chrome": "chrome",
                "google chrome": "chrome",
                "firefox": "firefox",
                "edge": "msedge",
                "microsoft edge": "msedge",
                "vscode": "code",
                "vs code": "code",
                "visual studio code": "code",
                "notepad": "notepad",
                "notepad++": "notepad++",
                "explorer": "explorer",
                "file explorer": "explorer",
                "calculator": "calc",
                "calc": "calc",
                "cmd": "cmd",
                "terminal": "wt",
                "windows terminal": "wt",
                "powershell": "powershell",
                "paint": "mspaint",
                "word": "winword",
                "excel": "excel",
                "powerpoint": "powerpnt",
                "spotify": "spotify",
                "discord": "discord",
                "slack": "slack",
                "teams": "teams",
            }

            # Resolve app name
            resolved = app_map.get(name.lower(), name)

            import webbrowser
            import urllib.parse
            
            # If it's a browser app with a URL or web query
            if resolved in ("chrome", "msedge", "firefox") or "http" in args:
                if args.startswith(("http://", "https://")) and "search_query" in args:
                    target_url = args
                elif args:
                    import re
                    q = args
                    q = re.sub(r'(?i)\b(https://|http://|www\.|open\s+chrome\s+and\s+|open\s+chrome\s+|open\s+browser\s+and\s+|open\s+browser\s+|search\s+youtube\s+for\s+|search\s+youtube\s+|search\s+google\s+for\s+|search\s+for\s+|search\s+|youtube\.com|youtube)\b', '', q)
                    clean_q = re.sub(r'\s+', ' ', q).strip(' /:')
                    if not clean_q:
                        clean_q = args.strip()
                    encoded = urllib.parse.quote_plus(clean_q)
                    
                    if "movie" in args.lower() or "karuppu" in args.lower() or "moviesda" in args.lower() or ("download" in args.lower() and not any(sw in args.lower() for sw in ["python", "vscode", "git", "node", "flutter", "java", "zoom"])):
                        target_url = "https://www.moviesda.studio/"
                        from app.tools.browser.browser_tools import open_in_chrome
                        open_in_chrome(target_url)
                        msg = f"Opened Chrome directly to Moviesda (https://www.moviesda.studio/) for '{clean_q}'"
                        logger.info(msg)
                        return ToolResult.ok(
                            data={"name": name, "url": target_url, "query": clean_q},
                            message=msg,
                        )
                    elif "youtube" in args.lower() or "video" in args.lower() or "dsa" in args.lower() or "tamil" in args.lower():
                        target_url = f"https://www.youtube.com/results?search_query={encoded}"
                    else:
                        target_url = f"https://www.google.com/search?q={encoded}"
                else:
                    target_url = "https://www.google.com"
                
                from app.tools.browser.browser_tools import open_in_chrome
                open_in_chrome(target_url)

                msg = f"Opened {name} visually at {target_url}"
                logger.info(msg)
                return ToolResult.ok(
                    data={"name": name, "url": target_url},
                    message=msg,
                )


            # Try dynamic app discovery for any installed or newly downloaded application
            target_path = None
            if os.path.isabs(resolved) and os.path.exists(resolved):
                target_path = resolved
            else:
                target_path = find_installed_app(name) or find_installed_app(resolved)

            if target_path:
                try:
                    os.startfile(target_path)
                except Exception:
                    os.system(f'start "" "{target_path}" {args}'.strip())
                time.sleep(1.0)
                msg = f"Launched application '{name}' from: {target_path}"
                logger.info(msg)
                return ToolResult.ok(
                    data={"name": name, "path": target_path},
                    message=msg,
                )

            # Fallback standard system launch
            try:
                if args:
                    os.system(f'start "" "{resolved}" {args}')
                else:
                    os.system(f'start "" "{resolved}"')
                
                time.sleep(1.0)
                msg = f"Launched {name} on desktop"
                logger.info(msg)
                return ToolResult.ok(
                    data={"name": name},
                    message=msg,
                )
            except Exception as ex:
                subprocess.Popen(
                    f"{resolved} {args}".strip(),
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                msg = f"Launched {name} (process created)"
                logger.info(msg)
                return ToolResult.ok(
                    data={"name": name},
                    message=msg,
                )

        except Exception as e:
            return ToolResult.fail(f"Failed to launch {name}: {e}")


class AppListTool(Tool):
    @property
    def name(self) -> str:
        return "app.list"

    @property
    def description(self) -> str:
        return "List currently running applications (visible windows)."

    @property
    def parameters(self) -> list[ToolParameter]:
        return []

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.LOW

    async def execute(self, **params: Any) -> ToolResult:
        try:
            import pygetwindow as gw
            
            apps = []
            seen = set()
            for w in gw.getAllWindows():
                if w.title and w.title.strip() and w.visible:
                    title = w.title.strip()
                    if title not in seen:
                        seen.add(title)
                        apps.append({"title": title})

            return ToolResult.ok(
                data={"applications": apps, "count": len(apps)},
                message=f"Found {len(apps)} running applications",
            )
        except Exception as e:
            return ToolResult.fail(str(e))


class AppCloseTool(Tool):
    @property
    def name(self) -> str:
        return "app.close"

    @property
    def description(self) -> str:
        return "Close an application by window title."

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="title", type="string",
                description="Window title of the app to close (partial match)",
            ),
        ]

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.MEDIUM

    async def execute(self, **params: Any) -> ToolResult:
        try:
            import pygetwindow as gw
            
            title = params.get("title", "")
            if not title:
                return ToolResult.fail("No window title provided")

            matching = [
                w for w in gw.getAllWindows()
                if title.lower() in w.title.lower() and w.title.strip()
            ]

            if not matching:
                return ToolResult.fail(f"No window matching: {title}")

            for w in matching:
                w.close()
                logger.info(f"Closed: {w.title}")

            return ToolResult.ok(
                message=f"Closed {len(matching)} window(s) matching '{title}'",
            )
        except Exception as e:
            return ToolResult.fail(str(e))


class AppFocusTool(Tool):
    @property
    def name(self) -> str:
        return "app.focus"

    @property
    def description(self) -> str:
        return "Bring an application window to the foreground."

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="title", type="string",
                description="Window title to focus (partial match)",
            ),
        ]

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.LOW

    async def execute(self, **params: Any) -> ToolResult:
        try:
            import pygetwindow as gw
            
            title = params.get("title", "")
            if not title:
                return ToolResult.fail("No window title provided")

            matching = [
                w for w in gw.getAllWindows()
                if title.lower() in w.title.lower() and w.title.strip()
            ]

            if not matching:
                return ToolResult.fail(f"No window matching: {title}")

            window = matching[0]
            if window.isMinimized:
                window.restore()
            window.activate()
            logger.info(f"Focused: {window.title}")
            return ToolResult.ok(
                data={"title": window.title},
                message=f"Focused: {window.title}",
            )
        except Exception as e:
            return ToolResult.fail(str(e))


class AppScanInstalledTool(Tool):
    @property
    def name(self) -> str:
        return "app.scan_installed"

    @property
    def description(self) -> str:
        return "Scan and list all installed applications on the computer."

    @property
    def parameters(self) -> list[ToolParameter]:
        return []

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.LOW

    async def execute(self, **params: Any) -> ToolResult:
        try:
            apps = get_all_installed_apps()
            return ToolResult.ok(
                data={"installed_apps": apps, "count": len(apps)},
                message=f"Discovered {len(apps)} installed applications",
            )
        except Exception as e:
            return ToolResult.fail(f"Failed to scan installed apps: {e}")


def get_tools() -> list[Tool]:
    return [AppLaunchTool(), AppListTool(), AppCloseTool(), AppFocusTool(), AppScanInstalledTool()]
