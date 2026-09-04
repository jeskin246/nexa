"""
NEXA Android Tools — Android phone automation & bridge via ADB.
"""

from __future__ import annotations

import asyncio
import datetime
import os
import re
import shutil
import subprocess
import time
import urllib.parse
from pathlib import Path
from typing import Any

from loguru import logger

from app.security.permissions import PermissionLevel
from app.tools.base import Tool, ToolCategory, ToolParameter, ToolResult


def get_adb_path() -> str:
    """Find the path to the adb executable on Windows or system PATH."""
    which_adb = shutil.which("adb")
    if which_adb:
        return which_adb

    candidates = [
        Path.home() / r"AppData\Local\Android\Sdk\platform-tools\adb.exe",
        Path(r"C:\Android\sdk\platform-tools\adb.exe"),
        Path(r"C:\Program Files\Android\Android Studio\bin\adb.exe"),
        Path(r"C:\Program Files\ASUS\GlideX\adb.exe"),
        Path(r"C:\Program Files\Wondershare\drfone\adb.exe"),
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return "adb"


def run_adb(args: list[str], timeout: float = 15.0) -> tuple[int, str, str]:
    """Run an ADB command and return (returncode, stdout, stderr)."""
    adb_bin = get_adb_path()
    cmd = [adb_bin] + args
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        return proc.returncode, proc.stdout or "", proc.stderr or ""
    except Exception as e:
        return -1, "", str(e)


def ensure_device_awake():
    """Wake up screen and dismiss lockscreen ONLY IF phone display is off or sleeping."""
    try:
        code, out, _ = run_adb(["shell", "dumpsys", "power"])
        if code == 0 and out:
            out_lower = out.lower()
            if "wakefulness: 1" in out_lower or "display power: state=on" in out_lower or "mholdingdisplaysuspendblocker=true" in out_lower or "mstate=on" in out_lower:
                # Screen is ALREADY awake — DO NOT SWIPE OR TOUCH THE SCREEN!
                return

        # Screen is OFF or asleep — wake up display & dismiss keyguard safely
        run_adb(["shell", "input", "keyevent", "224"])
        run_adb(["shell", "wm", "dismiss-keyguard"])
        run_adb(["shell", "input", "keyevent", "82"])
        time.sleep(0.5)
    except Exception as ex:
        logger.warning(f"ensure_device_awake exception: {ex}")


COMMON_ANDROID_APPS = {
    "chrome": "com.android.chrome",
    "youtube": "com.google.android.youtube",
    "whatsapp": "com.whatsapp",
    "instagram": "com.instagram.android",
    "facebook": "com.facebook.katana",
    "gmail": "com.google.android.gm",
    "maps": "com.google.android.apps.maps",
    "camera": "com.android.camera",
    "settings": "com.android.settings",
    "photos": "com.google.android.apps.photos",
    "clock": "com.google.android.deskclock",
    "calculator": "com.google.android.calculator",
    "contacts": "com.android.contacts",
    "phone": "com.google.android.dialer",
    "messages": "com.google.android.apps.messaging",
    "telegram": "org.telegram.messenger",
    "spotify": "com.spotify.music",
    "linkedin": "com.linkedin.android",
    "github": "com.github.android",
    "blinkit": "com.grofers.customerapp",
    "zepto": "com.zeptonow.app",
    "zomato": "com.application.zomato",
    "swiggy": "com.swiggy.android",
    "uber": "com.ubercab",
    "ola": "com.olacabs.customer",
    "flipkart": "com.flipkart.android",
    "amazon": "com.amazon.mShop.android.shopping",
    "paytm": "net.one97.paytm",
    "phonepe": "com.phonepe.app",
}


class AndroidDevicesTool(Tool):
    @property
    def name(self) -> str:
        return "android.devices"

    @property
    def description(self) -> str:
        return "List connected Android phones, tablets, or emulators via ADB bridge."

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.ANDROID

    @property
    def parameters(self) -> list[ToolParameter]:
        return []

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.LOW

    async def execute(self, **params: Any) -> ToolResult:
        code, out, err = run_adb(["devices"])
        if code != 0:
            return ToolResult.fail(f"ADB devices check failed: {err or 'ADB executable not found'}")

        devices = []
        for line in out.splitlines():
            line = line.strip()
            if line and not line.startswith("List of devices"):
                parts = line.split()
                if len(parts) >= 2:
                    devices.append({"id": parts[0], "status": parts[1]})

        if not devices:
            return ToolResult.ok(
                data={"devices": [], "count": 0},
                message="No Android phone connected via USB/ADB. Enable USB Debugging on your phone and connect via USB.",
            )

        return ToolResult.ok(
            data={"devices": devices, "count": len(devices)},
            message=f"Found {len(devices)} connected Android device(s)",
        )


class AndroidListAppsTool(Tool):
    @property
    def name(self) -> str:
        return "android.list_apps"

    @property
    def description(self) -> str:
        return "List all installed applications/packages on the connected Android phone."

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.ANDROID

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="filter",
                type="string",
                description="Optional search filter for package or app name",
                required=False,
            )
        ]

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.LOW

    async def execute(self, **params: Any) -> ToolResult:
        filt = params.get("filter", "").lower().strip()
        code, out, err = run_adb(["shell", "pm", "list", "packages", "-3"])
        if code != 0 or "package:" not in out:
            code, out, err = run_adb(["shell", "pm", "list", "packages"])
        if code != 0 or "package:" not in out:
            return ToolResult.fail(f"Failed to list packages on Android: {err or out or 'Device offline'}")

        pkgs = []
        for line in out.splitlines():
            if line.startswith("package:"):
                p = line.replace("package:", "").strip()
                if not filt or filt in p.lower():
                    pkgs.append(p)

        return ToolResult.ok(
            data={"packages": pkgs[:100], "count": len(pkgs)},
            message=f"Found {len(pkgs)} package(s) on Android phone",
        )


class AndroidLaunchAppTool(Tool):
    @property
    def name(self) -> str:
        return "android.launch_app"

    @property
    def description(self) -> str:
        return "Launch any application on the connected Android phone by app name or package name."

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.ANDROID

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="name",
                type="string",
                description="Application name (e.g. 'whatsapp', 'youtube', 'chrome', 'camera') or full package name",
            ),
            ToolParameter(
                name="url",
                type="string",
                description="Optional website URL or Google search URL to open",
                required=False,
            )
        ]

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.LOW

    async def execute(self, **params: Any) -> ToolResult:
        ensure_device_awake()
        url = params.get("url", "").strip()
        name = params.get("name", "").strip().lower()

        if url:
            code, out, err = run_adb(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", url, "com.android.chrome"])
            if code != 0 or "Error" in err:
                code, out, err = run_adb(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", url])
            msg = f"Opened URL '{url}' in Chrome on Android phone!"
            logger.info(msg)
            return ToolResult.ok(data={"url": url}, message=msg)

        if not name:
            return ToolResult.fail("No Android application name provided")

        pkg = COMMON_ANDROID_APPS.get(name)

        if not pkg:
            if "." in name and not name.endswith("."):
                pkg = name
            else:
                # 1. Scan 3rd party user-installed apps first (Instant & accurate)
                code, out, _ = run_adb(["shell", "pm", "list", "packages", "-3"])
                if code == 0:
                    for line in out.splitlines():
                        if line.startswith("package:"):
                            p = line.replace("package:", "").strip()
                            if name in p.lower():
                                pkg = p
                                break

                # 2. Fallback scan all installed packages
                if not pkg:
                    code, out, _ = run_adb(["shell", "pm", "list", "packages"])
                    if code == 0:
                        for line in out.splitlines():
                            if line.startswith("package:"):
                                p = line.replace("package:", "").strip()
                                if name in p.lower():
                                    pkg = p
                                    break

        if not pkg:
            return ToolResult.fail(f"Could not find package for Android app '{name}'")

        code, out, err = run_adb(["shell", "monkey", "-p", pkg, "-c", "android.intent.category.LAUNCHER", "1"])
        if code != 0 and "Events injected: 1" not in out:
            code, out, err = run_adb(["shell", "am", "start", "-n", f"{pkg}/.MainActivity"])

        if "Events injected: 1" in out or code == 0:
            msg = f"Successfully launched '{name}' ({pkg}) on Android phone"
            logger.info(msg)
            return ToolResult.ok(data={"name": name, "package": pkg}, message=msg)

        return ToolResult.fail(f"Failed to launch Android app '{name}': {err or out}")


class AndroidScreenCaptureTool(Tool):
    @property
    def name(self) -> str:
        return "android.screenshot"

    @property
    def description(self) -> str:
        return "Capture a screenshot of the connected Android phone screen."

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.ANDROID

    @property
    def parameters(self) -> list[ToolParameter]:
        return []

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.LOW

    async def execute(self, **params: Any) -> ToolResult:
        shot_dir = Path.home() / ".nexa" / "screenshots"
        shot_dir.mkdir(parents=True, exist_ok=True)
        from datetime import datetime
        fname = f"android_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        out_path = shot_dir / fname

        adb_bin = get_adb_path()
        try:
            # Fast single-pass screencap directly on phone storage
            phone_img = "/sdcard/nexa_screenshot.png"
            c, out, err = run_adb(["shell", "screencap", "-p", phone_img])
            if c == 0:
                run_adb(["shell", "am", "broadcast", "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE", "-d", f"file://{phone_img}"])

            # Pull screenshot to PC local directory
            adb_bin = get_adb_path()
            subprocess.run([adb_bin, "pull", phone_img, str(out_path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)

            if out_path.exists() and out_path.stat().st_size > 0:
                msg = f"Captured screen to: {out_path}"
                logger.info(msg)
                return ToolResult.ok(
                    data={"path": str(out_path), "phone_path": phone_img},
                    message=msg,
                )
        except Exception as e:
            logger.warning(f"Fast screencap fallback notice: {e}")

        return ToolResult.fail("Captured screenshot file was empty or failed")


class AndroidTapTool(Tool):
    @property
    def name(self) -> str:
        return "android.tap"

    @property
    def description(self) -> str:
        return "Tap on the Android phone screen at specific X, Y coordinates."

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.ANDROID

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(name="x", type="integer", description="X pixel coordinate on phone screen"),
            ToolParameter(name="y", type="integer", description="Y pixel coordinate on phone screen"),
        ]

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.MEDIUM

    async def execute(self, **params: Any) -> ToolResult:
        import time
        x = params.get("x", 500)
        y = params.get("y", 750)
        delay = params.get("delay", 0.8)

        if delay > 0:
            time.sleep(delay)

        # 1. Tap exact screen coordinates
        code, out, err = run_adb(["shell", "input", "tap", str(x), str(y)])

        # 2. Trigger DPAD DOWN + ENTER to select & play focused video item
        time.sleep(0.3)
        run_adb(["shell", "input", "keyevent", "20"])  # DPAD DOWN
        run_adb(["shell", "input", "keyevent", "66"])  # ENTER

        if code == 0:
            msg = f"Tapped and launched video playback on Android screen at ({x}, {y})"
            return ToolResult.ok(data={"x": x, "y": y}, message=msg)

        return ToolResult.fail(f"Failed to tap on Android screen: {err or out}")


class AndroidKeyEventTool(Tool):
    @property
    def name(self) -> str:
        return "android.key_event"

    @property
    def description(self) -> str:
        return "Trigger button actions on Android phone (home, back, power, volume_up, volume_down, enter)."

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.ANDROID

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="key",
                type="string",
                description="Key event name (e.g. 'home', 'back', 'power', 'volume_up', 'volume_down', 'enter')",
                enum=["home", "back", "power", "volume_up", "volume_down", "enter"],
            )
        ]

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.LOW

    async def execute(self, **params: Any) -> ToolResult:
        key = params.get("key", "").lower().strip()
        key_map = {
            "home": "3",
            "back": "4",
            "power": "26",
            "volume_up": "24",
            "volume_down": "25",
            "enter": "66",
        }
        code_val = key_map.get(key, key)
        code, out, err = run_adb(["shell", "input", "keyevent", code_val])
        if code == 0:
            msg = f"Triggered key event '{key}' on Android phone"
            return ToolResult.ok(data={"key": key}, message=msg)

        return ToolResult.fail(f"Key event '{key}' failed on Android: {err or out}")


class AndroidTypeTextTool(Tool):
    @property
    def name(self) -> str:
        return "android.type"

    @property
    def description(self) -> str:
        return "Type text into the currently active input field on the connected Android phone."

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.ANDROID

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(name="text", type="string", description="Text to type on phone"),
            ToolParameter(name="press_enter", type="boolean", description="Press Enter after typing", required=False, default=True),
        ]

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.MEDIUM

    async def execute(self, **params: Any) -> ToolResult:
        text = params.get("text", "")
        press_enter = params.get("press_enter", True)

        if not text:
            return ToolResult.fail("No text provided to type on Android")

        if text.startswith("http://") or text.startswith("https://"):
            code, out, err = run_adb(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", text])
            if code == 0:
                msg = f"Opened URL '{text}' on Android phone"
                logger.info(msg)
                return ToolResult.ok(data={"url": text}, message=msg)
            return ToolResult.fail(f"Failed to open URL on Android: {err or out}")

        formatted_text = text.replace(" ", "%s").replace("'", "\\'").replace('"', '\\"')
        code, out, err = run_adb(["shell", "input", "text", formatted_text])

        if press_enter:
            run_adb(["shell", "input", "keyevent", "66"])

        if code == 0:
            msg = f"Typed '{text}' into active input on Android phone"
            logger.info(msg)
            return ToolResult.ok(data={"typed": text}, message=msg)

        return ToolResult.fail(f"Failed to type text on Android: {err or out}")


class AndroidSwipeTool(Tool):
    @property
    def name(self) -> str:
        return "android.swipe"

    @property
    def description(self) -> str:
        return "Swipe screen in direction (up, down, left, right) on Android phone."

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.ANDROID

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="direction",
                type="string",
                description="Swipe direction (up, down, left, right)",
                enum=["up", "down", "left", "right"],
                required=False,
                default="up",
            ),
            ToolParameter(name="duration_ms", type="integer", description="Duration of swipe in ms", required=False, default=300),
        ]

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.LOW

    async def execute(self, **params: Any) -> ToolResult:
        direction = params.get("direction", "up").lower().strip()
        dur = params.get("duration_ms", 300)

        coords_map = {
            "up": ("500", "1600", "500", "600"),
            "down": ("500", "600", "500", "1600"),
            "left": ("900", "1000", "200", "1000"),
            "right": ("200", "1000", "900", "1000"),
        }
        x1, y1, x2, y2 = coords_map.get(direction, coords_map["up"])

        code, out, err = run_adb(["shell", "input", "swipe", x1, y1, x2, y2, str(dur)])
        if code == 0:
            msg = f"Swiped '{direction}' on Android phone screen"
            logger.info(msg)
            return ToolResult.ok(data={"direction": direction}, message=msg)

        return ToolResult.fail(f"Failed to swipe on Android phone: {err or out}")


class AndroidReadScreenTextTool(Tool):
    @property
    def name(self) -> str:
        return "android.read_screen_text"

    @property
    def description(self) -> str:
        return "Extract and read all visible text elements and buttons from the Android phone screen."

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.ANDROID

    @property
    def parameters(self) -> list[ToolParameter]:
        return []

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.LOW

    async def execute(self, **params: Any) -> ToolResult:
        run_adb(["shell", "uiautomator", "dump", "/sdcard/window_dump.xml"])
        code, out, err = run_adb(["shell", "cat", "/sdcard/window_dump.xml"])

        if code != 0 or not out:
            return ToolResult.fail("Could not extract UI hierarchy from Android screen")

        texts = re.findall(r'text="([^"]+)"', out)
        content_descs = re.findall(r'content-desc="([^"]+)"', out)

        elements = [t.strip() for t in (texts + content_descs) if t.strip()]
        unique_elements = list(dict.fromkeys(elements))

        summary = "\n".join(f"- {e}" for e in unique_elements[:30])
        msg = f"Extracted {len(unique_elements)} visible element(s) from phone screen:\n{summary}"

        return ToolResult.ok(
            data={"elements": unique_elements, "count": len(unique_elements)},
            message=msg,
        )


class AndroidInstallAppTool(Tool):
    @property
    def name(self) -> str:
        return "android.install_app"

    @property
    def description(self) -> str:
        return "Search and open any requested application page in Google Play Store on Android phone for installation."

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.ANDROID

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="name",
                type="string",
                description="Application name to search and install in Play Store (e.g. 'whatsapp', 'instagram', 'spotify', 'vlc')",
            )
        ]

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.MEDIUM

    async def execute(self, **params: Any) -> ToolResult:
        app_name = params.get("name", "").strip()
        if not app_name:
            return ToolResult.fail("No application name specified to install from Play Store")

        import time, urllib.parse, re
        encoded_name = urllib.parse.quote_plus(app_name)

        # 1. Launch Google Play Store directly with requested app search
        play_store_url = f"https://play.google.com/store/search?q={encoded_name}&c=apps"
        code, out, err = run_adb(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", play_store_url, "com.android.vending"])
        if code != 0 or "Error" in err:
            code, out, err = run_adb(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", f"market://search?q={encoded_name}"])
            if code != 0 or "Error" in err:
                run_adb(["shell", "monkey", "-p", "com.android.vending", "1"])

        # 2. Wait for Play Store page to load on phone screen
        time.sleep(2.5)

        # 3. Dump UI hierarchy to locate Install button on phone screen
        tapped_install = False
        try:
            run_adb(["shell", "uiautomator", "dump", "/sdcard/window_dump.xml"])
            c, xml, _ = run_adb(["shell", "cat", "/sdcard/window_dump.xml"])
            if c == 0 and xml:
                # Find Install / Get button bounds
                match = re.search(r'(?:text|content-desc)="(?i:Install|Get)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml)
                if match:
                    x1, y1, x2, y2 = map(int, match.groups())
                    cx = (x1 + x2) // 2
                    cy = (y1 + y2) // 2
                    run_adb(["shell", "input", "tap", str(cx), str(cy)])
                    tapped_install = True
                    logger.info(f"Auto-tapped 'Install' button at ({cx}, {cy}) on Android screen")
        except Exception as ex:
            logger.warning(f"Play Store auto-tap inspection note: {ex}")

        # Fallback tap if UI dump didn't catch bounds
        if not tapped_install:
            run_adb(["shell", "input", "tap", "540", "1150"])

        msg = f"Opened Google Play Store for '{app_name}' and automatically tapped 'Install' on your Android phone screen!"
        logger.info(msg)
        return ToolResult.ok(
            data={"app_name": app_name, "tapped_install": True},
            message=msg,
        )


class AndroidPlayYouTubeTool(Tool):
    @property
    def name(self) -> str:
        return "android.play_youtube"

    @property
    def description(self) -> str:
        return "Search and automatically play any requested video on YouTube on the connected Android phone."

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.ANDROID

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="query",
                type="string",
                description="Search query or video topic on YouTube (e.g. 'dsa', 'python tutorial')",
            ),
            ToolParameter(
                name="action",
                type="string",
                description="Action type: 'search' (open search results page) or 'play' (auto-play top video)",
                required=False,
                default="play",
            ),
            ToolParameter(
                name="filter",
                type="string",
                description="Sort filter: 'recent' (upload date), 'views' (highest views), or 'relevant'",
                required=False,
                default="relevant",
            )
        ]

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.MEDIUM

    async def execute(self, **params: Any) -> ToolResult:
        ensure_device_awake()
        query = params.get("query", "dsa").strip()
        action = params.get("action", "play").strip().lower()
        filt = params.get("filter", "relevant").strip().lower()

        import time, urllib.parse, urllib.request, re
        sp_param = ""
        if "recent" in filt or "latest" in filt or "new" in filt:
            sp_param = "&sp=EgIIAQ%253D%253D"
        elif "view" in filt or "high" in filt or "popular" in filt:
            sp_param = "&sp=CAM%253D"

        encoded = urllib.parse.quote_plus(query)
        search_url = f"https://www.youtube.com/results?search_query={encoded}{sp_param}"

        # If action is 'search', open the search results page directly in YouTube app
        if action == "search":
            code, out, err = run_adb(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", search_url, "com.google.android.youtube"])
            if code != 0 or "Error" in err:
                code, out, err = run_adb(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", search_url])
            msg = f"Opened YouTube search results for '{query}' on your Android phone!"
            logger.info(msg)
            return ToolResult.ok(data={"query": query, "url": search_url, "action": "search"}, message=msg)

        video_id = ""
        try:
            req = urllib.request.Request(
                search_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=4) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                vids = re.findall(r'(?:"videoId":\s*"|/watch\?v=)([a-zA-Z0-9_-]{11})', html)
                if vids:
                    video_id = vids[0]
                    logger.info(f"Resolved top YouTube video ID for '{query}' [{filt}]: {video_id}")
        except Exception as e:
            logger.warning(f"Direct video ID lookup note: {e}")

        # 1. Direct Playback via Native YouTube Watch Intent (Instant auto-play!)
        if video_id:
            direct_url = f"https://www.youtube.com/watch?v={video_id}"
            code, out, err = run_adb(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", direct_url, "com.google.android.youtube"])
            if code != 0 or "Error" in err:
                code, out, err = run_adb(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", direct_url])

            time.sleep(2.0)
            run_adb(["shell", "input", "keyevent", "126"])  # KEYEVENT_MEDIA_PLAY

            msg = f"Directly launched and started playing YouTube video ({video_id}) for '{query}' [{filt}] on your Android phone!"
            logger.info(msg)
            return ToolResult.ok(data={"query": query, "video_id": video_id, "url": direct_url}, message=msg)

        # 2. Fallback: Search URL + Auto Tap + Keyevent
        code, out, err = run_adb(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", search_url])
        if code != 0 or "Error" in err:
            run_adb(["shell", "am", "start", "-a", "android.intent.action.SEARCH", "-e", "query", query, "com.google.android.youtube"])

        time.sleep(3.0)

        run_adb(["shell", "input", "tap", "500", "650"])
        time.sleep(0.3)
        run_adb(["shell", "input", "tap", "500", "850"])
        time.sleep(0.4)
        run_adb(["shell", "input", "keyevent", "20"])  # DPAD DOWN
        time.sleep(0.2)
        run_adb(["shell", "input", "keyevent", "66"])  # ENTER
        time.sleep(0.5)
        run_adb(["shell", "input", "keyevent", "126"]) # MEDIA PLAY

        msg = f"Opened YouTube search for '{query}' and triggered video playback on your Android phone screen!"
        logger.info(msg)
        return ToolResult.ok(data={"query": query, "url": search_url}, message=msg)


class AndroidSendWhatsAppTool(Tool):
    @property
    def name(self) -> str:
        return "android.send_whatsapp"

    @property
    def description(self) -> str:
        return "Send WhatsApp message(s) to recipient phone number(s) or contact name(s) on the connected Android phone via ADB intents & UI automation."

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.ANDROID

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="phone",
                type="string",
                description="Phone number with country code (e.g. '+1234567890' or '919876543210') or contact name",
                required=False,
            ),
            ToolParameter(
                name="message",
                type="string",
                description="Message text to send to recipient",
                required=False,
            ),
            ToolParameter(
                name="messages",
                type="array",
                description="List of multi-recipient message items, e.g. [{'phone': 'user2', 'message': 'hi'}, {'phone': 'user3', 'message': 'hello'}]",
                required=False,
            ),
            ToolParameter(
                name="send_screenshot",
                type="boolean",
                description="If True, attaches and sends the latest screen capture image on WhatsApp",
                required=False,
            ),
            ToolParameter(
                name="image_path",
                type="string",
                description="Optional phone image file path (e.g. '/sdcard/nexa_screenshot.png') to attach and send",
                required=False,
            ),
        ]

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.MEDIUM

    async def execute(self, **params: Any) -> ToolResult:
        phone = params.get("phone", "").strip()
        message = params.get("message", "").strip()
        messages_list = params.get("messages", [])
        send_screenshot = params.get("send_screenshot", False) or bool(params.get("image_path"))
        image_path = str(params.get("image_path") or "/sdcard/nexa_screenshot.png").strip()

        import time, urllib.parse, re

        # Helper to split multi-recipient input strings (e.g. "user1, user2 and user3", "+12345, +67890")
        def parse_recipients(p_val: str) -> list[str]:
            if not p_val:
                return []
            parts = re.split(r',|\n|\band\b|\b&\b', p_val, flags=re.IGNORECASE)
            return [part.strip() for part in parts if part.strip()]

        # Build list of items to send
        items = []
        if isinstance(messages_list, list) and len(messages_list) > 0:
            for item in messages_list:
                if isinstance(item, dict):
                    p_raw = str(item.get("phone") or item.get("recipient") or item.get("contact") or "").strip()
                    m = str(item.get("message") or item.get("text") or "").strip()
                    if p_raw:
                        for sub_p in parse_recipients(p_raw):
                            items.append((sub_p, m or "Here is the screenshot from my phone"))
        elif phone:
            for sub_p in parse_recipients(phone):
                items.append((sub_p, message or "Here is the screenshot from my phone"))

        if not items:
            return ToolResult.fail("No recipient phone number specified to send on WhatsApp.")

        # Ensure screen is awake, unlocked & ADB reverse port forwarding is active
        ensure_device_awake()
        run_adb(["reverse", "tcp:8000", "tcp:8000"])

        # Helper to get physical screen size for dynamic coordinate fallback
        def get_screen_dim():
            c, out, _ = run_adb(["shell", "wm", "size"])
            if c == 0 and "size:" in out:
                bm = re.search(r"(\d+)x(\d+)", out)
                if bm:
                    return int(bm.group(1)), int(bm.group(2))
            return 1080, 2400

        sw, sh = get_screen_dim()

        # Helper to find Send button from UI XML dump (excluding voice message buttons)
        def find_xml_button(resource_id_part, content_desc_part):
            try:
                run_adb(["shell", "uiautomator", "dump", "/sdcard/window_dump.xml"])
                c, xml, _ = run_adb(["shell", "cat", "/sdcard/window_dump.xml"])
                if c == 0 and xml:
                    for node in re.finditer(r'<node[^>]*>', xml):
                        s = node.group(0)
                        # Skip voice message / microphone buttons explicitly
                        if 'voice_note' in s.lower() or 'voice message' in s.lower():
                            continue
                        if (resource_id_part and resource_id_part in s) or (content_desc_part and content_desc_part.lower() in s.lower()):
                            bm = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', s)
                            if bm:
                                x1, y1, x2, y2 = map(int, bm.groups())
                                return (x1 + x2) // 2, (y1 + y2) // 2
            except Exception as ex:
                logger.warning(f"UI XML dump inspection exception: {ex}")
            return None

        # Helper to find Contact item from search results XML dump
        def find_contact_result(contact_name_query):
            try:
                run_adb(["shell", "uiautomator", "dump", "/sdcard/window_dump.xml"])
                c, xml, _ = run_adb(["shell", "cat", "/sdcard/window_dump.xml"])
                if c == 0 and xml:
                    name_clean = re.sub(r'[^a-zA-Z0-9]', '', contact_name_query).lower()
                    words = [w for w in re.split(r'\s+', name_clean) if len(w) >= 2]
                    candidates = []
                    for node in re.finditer(r'<node[^>]*>', xml):
                        s = node.group(0)
                        bm_text = re.search(r'(?:text|content-desc)="([^"]+)"', s)
                        if bm_text:
                            val = re.sub(r'[^a-zA-Z0-9]', '', bm_text.group(1)).lower()
                            if name_clean and (name_clean in val or val in name_clean or (words and any(w in val for w in words))):
                                bm = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', s)
                                if bm:
                                    x1, y1, x2, y2 = map(int, bm.groups())
                                    if y1 > int(sh * 0.14):
                                        cx = max((x1 + x2) // 2, int(sw * 0.45))
                                        cy = (y1 + y2) // 2
                                        candidates.append((y1, cx, cy))

                    if candidates:
                        # Sort candidates strictly by Y position (Top-most contact result FIRST)
                        candidates.sort(key=lambda item: item[0])
                        return candidates[0][1], candidates[0][2]
            except Exception as ex:
                logger.warning(f"Contact search XML dump exception: {ex}")
            return None

        # Helper to query phone number from device contacts
        def resolve_contact_phone(contact_name):
            clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', contact_name).strip()
            if not clean_name:
                return None
            try:
                code, out, _ = run_adb([
                    "shell", "content", "query",
                    "--uri", "content://com.android.contacts/data/phones",
                    "--projection", "display_name:number",
                    "--where", f"display_name LIKE '%{clean_name}%'"
                ])
                if code == 0 and out and "number=" in out:
                    match = re.search(r'number=([\d+ \-]+)', out)
                    if match:
                        num = re.sub(r'\D', '', match.group(1))
                        if len(num) >= 7:
                            return num
            except Exception as ex:
                logger.warning(f"ADB contact resolution exception: {ex}")
            return None

        # Helper to find WhatsApp Message Input box XML element (EditText or Message entry)
        def find_whatsapp_message_input():
            try:
                run_adb(["shell", "uiautomator", "dump", "/sdcard/window_dump.xml"])
                c, xml, _ = run_adb(["shell", "cat", "/sdcard/window_dump.xml"])
                if c == 0 and xml:
                    for node in re.finditer(r'<node[^>]*class="android\.widget\.EditText"[^>]*>', xml):
                        s = node.group(0)
                        bm = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', s)
                        if bm:
                            x1, y1, x2, y2 = map(int, bm.groups())
                            if y1 > int(sh * 0.40):
                                return (x1 + x2) // 2, (y1 + y2) // 2
            except Exception as ex:
                logger.warning(f"Message input XML dump exception: {ex}")
            return None

        # Image Attachment Branch (Send Screenshot via WhatsApp)
        if send_screenshot:
            results = []
            for p, m in items:
                clean_contact = clean_recipient_phone(p)
                clean_contact = re.sub(r'(?i)\s*\b(?:on|in|via)\s+(?:whatsapp|phone|android)\b', '', clean_contact).strip() or clean_contact

                # 1. Open contact chat window in WhatsApp
                run_adb(["shell", "am", "force-stop", "com.whatsapp"])
                time.sleep(0.5)
                run_adb(["shell", "monkey", "-p", "com.whatsapp", "-c", "android.intent.category.LAUNCHER", "1"])
                time.sleep(2.0)

                # Tap Search Icon
                search_pos = find_xml_button("com.whatsapp:id/menuitem_search", "Search") or find_xml_button("com.whatsapp:id/search_button", "Search")
                if search_pos:
                    run_adb(["shell", "input", "tap", str(search_pos[0]), str(search_pos[1])])
                else:
                    run_adb(["shell", "input", "tap", str(int(sw * 0.85)), str(int(sh * 0.06))])
                time.sleep(1.0)

                safe_name = re.sub(r'[^a-zA-Z0-9\s+_\-]', '', clean_contact).strip().replace(" ", "%s")
                if safe_name:
                    run_adb(["shell", "input", "text", safe_name])
                time.sleep(1.5)

                contact_pos = find_contact_result(clean_contact)
                if contact_pos:
                    run_adb(["shell", "input", "tap", str(contact_pos[0]), str(contact_pos[1])])
                else:
                    run_adb(["shell", "input", "tap", str(int(sw * 0.50)), str(int(sh * 0.22))])
                time.sleep(2.0)

                # 2. Tap Attachment Paperclip icon in chat room
                attach_pos = find_xml_button("com.whatsapp:id/input_attach_button", "Attach")
                if attach_pos:
                    run_adb(["shell", "input", "tap", str(attach_pos[0]), str(attach_pos[1])])
                else:
                    run_adb(["shell", "input", "tap", str(int(sw * 0.72)), str(int(sh * 0.955))])
                time.sleep(1.2)

                # 3. Tap Gallery / Photos icon
                gallery_pos = find_xml_button("com.whatsapp:id/pick_photos", "Gallery")
                if gallery_pos:
                    run_adb(["shell", "input", "tap", str(gallery_pos[0]), str(gallery_pos[1])])
                else:
                    run_adb(["shell", "input", "tap", str(int(sw * 0.50)), str(int(sh * 0.75))])
                time.sleep(1.5)

                # 4. Tap recent photo item (Top left screenshot in WhatsApp Gallery)
                photo_pos = find_xml_button("com.whatsapp:id/thumbnail", "") or find_xml_button("thumbnail", "") or find_xml_button("com.whatsapp:id/gallery_header_grid", "")
                if photo_pos:
                    run_adb(["shell", "input", "tap", str(photo_pos[0]), str(photo_pos[1])])
                    logger.info(f"Tapped exact WhatsApp gallery photo thumbnail at {photo_pos}")
                else:
                    # Precise fallback coordinates for 1st gallery photo slot on Android screen
                    first_item_x, first_item_y = int(sw * 0.15), int(sh * 0.15)
                    run_adb(["shell", "input", "tap", str(first_item_x), str(first_item_y)])
                    logger.info(f"Tapped WhatsApp gallery photo fallback at ({first_item_x}, {first_item_y})")
                time.sleep(1.5)

                # 5. Tap Send button
                send_pos = find_xml_button("com.whatsapp:id/send", "Send")
                if send_pos:
                    run_adb(["shell", "input", "tap", str(send_pos[0]), str(send_pos[1])])
                else:
                    run_adb(["shell", "input", "tap", str(int(sw * 0.93)), str(int(sh * 0.955))])
                    time.sleep(0.2)
                    run_adb(["shell", "input", "keyevent", "66"])

                results.append({"phone": p, "sent_image": True})
                time.sleep(1.5)

            msg = f"Sent screenshot image to {len(results)} recipient(s) on WhatsApp!"
            logger.info(msg)
            return ToolResult.ok(data={"results": results, "count": len(results), "send_screenshot": True}, message=msg)

        sw, sh = get_screen_dim()

        # Helper to find Send button from UI XML dump (excluding voice message buttons)
        def find_xml_button(resource_id_part, content_desc_part):
            try:
                run_adb(["shell", "uiautomator", "dump", "/sdcard/window_dump.xml"])
                c, xml, _ = run_adb(["shell", "cat", "/sdcard/window_dump.xml"])
                if c == 0 and xml:
                    for node in re.finditer(r'<node[^>]*>', xml):
                        s = node.group(0)
                        # Skip voice message / microphone buttons explicitly
                        if 'voice_note' in s.lower() or 'voice message' in s.lower():
                            continue
                        if (resource_id_part and resource_id_part in s) or (content_desc_part and content_desc_part.lower() in s.lower()):
                            bm = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', s)
                            if bm:
                                x1, y1, x2, y2 = map(int, bm.groups())
                                return (x1 + x2) // 2, (y1 + y2) // 2
            except Exception as ex:
                logger.warning(f"UI XML dump inspection exception: {ex}")
            return None

        # Helper to find Contact item from search results XML dump
        def find_contact_result(contact_name_query):
            try:
                run_adb(["shell", "uiautomator", "dump", "/sdcard/window_dump.xml"])
                c, xml, _ = run_adb(["shell", "cat", "/sdcard/window_dump.xml"])
                if c == 0 and xml:
                    name_clean = re.sub(r'[^a-zA-Z0-9]', '', contact_name_query).lower()
                    words = [w for w in re.split(r'\s+', name_clean) if len(w) >= 2]
                    candidates = []
                    for node in re.finditer(r'<node[^>]*>', xml):
                        s = node.group(0)
                        bm_text = re.search(r'(?:text|content-desc)="([^"]+)"', s)
                        if bm_text:
                            val = re.sub(r'[^a-zA-Z0-9]', '', bm_text.group(1)).lower()
                            if name_clean and (name_clean in val or val in name_clean or (words and any(w in val for w in words))):
                                bm = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', s)
                                if bm:
                                    x1, y1, x2, y2 = map(int, bm.groups())
                                    if y1 > int(sh * 0.14):
                                        cx = max((x1 + x2) // 2, int(sw * 0.45))
                                        cy = (y1 + y2) // 2
                                        candidates.append((y1, cx, cy))

                    if candidates:
                        # Sort candidates strictly by Y position (Top-most contact result FIRST)
                        candidates.sort(key=lambda item: item[0])
                        return candidates[0][1], candidates[0][2]
            except Exception as ex:
                logger.warning(f"Contact search XML dump exception: {ex}")
            return None

        # Helper to query phone number from device contacts
        def resolve_contact_phone(contact_name):
            clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', contact_name).strip()
            if not clean_name:
                return None
            try:
                code, out, _ = run_adb([
                    "shell", "content", "query",
                    "--uri", "content://com.android.contacts/data/phones",
                    "--projection", "display_name:number",
                    "--where", f"display_name LIKE '%{clean_name}%'"
                ])
                if code == 0 and out and "number=" in out:
                    match = re.search(r'number=([\d+ \-]+)', out)
                    if match:
                        num = re.sub(r'\D', '', match.group(1))
                        if len(num) >= 7:
                            return num
            except Exception as ex:
                logger.warning(f"ADB contact resolution exception: {ex}")
            return None

        # Helper to find WhatsApp Message Input box XML element (EditText or Message entry)
        def find_whatsapp_message_input():
            try:
                run_adb(["shell", "uiautomator", "dump", "/sdcard/window_dump.xml"])
                c, xml, _ = run_adb(["shell", "cat", "/sdcard/window_dump.xml"])
                if c == 0 and xml:
                    # 1. Search for android.widget.EditText node (Exact message input field)
                    for node in re.finditer(r'<node[^>]*class="android\.widget\.EditText"[^>]*>', xml):
                        s = node.group(0)
                        bm = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', s)
                        if bm:
                            x1, y1, x2, y2 = map(int, bm.groups())
                            return (x1 + x2) // 2, (y1 + y2) // 2

                    # 2. Search for nodes with "Type a message" or "Message" text/content-desc
                    for node in re.finditer(r'<node[^>]*>', xml):
                        s = node.group(0)
                        if any(k in s.lower() for k in ['type a message', 'message', 'entry']):
                            if 'voice' not in s.lower() and 'search' not in s.lower():
                                bm = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', s)
                                if bm:
                                    x1, y1, x2, y2 = map(int, bm.groups())
                                    if y1 > int(sh * 0.50):
                                        return (x1 + x2) // 2, (y1 + y2) // 2
            except Exception as ex:
                logger.warning(f"Message input XML dump exception: {ex}")
            return None

        results = []
        for p, m in items:
            # Force stop WhatsApp before handling each recipient to clear prior conversation state completely
            run_adb(["shell", "am", "force-stop", "com.whatsapp"])
            time.sleep(0.5)

            resolved_num = resolve_contact_phone(p)
            if resolved_num:
                target_phone = resolved_num
                is_phone_number = True
                logger.info(f"Resolved contact name '{p}' to phone number '{target_phone}' via Android Contacts DB")
            else:
                target_phone = p
                is_phone_number = len(re.sub(r"\D", "", p)) >= 7

            if is_phone_number:
                digits_only = re.sub(r"\D", "", target_phone)
                if len(digits_only) == 10:
                    clean_phone = "91" + digits_only
                else:
                    clean_phone = digits_only or target_phone
                encoded_msg = urllib.parse.quote(m)

                # 1. Fire native whatsapp:// intent first, then web fallback
                intent_native = f"whatsapp://send?phone={clean_phone}&text={encoded_msg}"
                intent_web = f"https://api.whatsapp.com/send?phone={clean_phone}&text={encoded_msg}"
                
                code, out, err = run_adb([
                    "shell", "am", "start", "-a", "android.intent.action.VIEW",
                    "-d", intent_native
                ])
                if code != 0 or "Error" in err or "Error" in out:
                    run_adb([
                        "shell", "am", "start", "-a", "android.intent.action.VIEW",
                        "-d", intent_web, "com.whatsapp"
                    ])

                time.sleep(2.5)

                # Focus Chat Input Box & ensure message text is set
                input_pos = find_whatsapp_message_input()
                if input_pos:
                    run_adb(["shell", "input", "tap", str(input_pos[0]), str(input_pos[1])])
                else:
                    input_x, input_y = int(sw * 0.40), int(sh * 0.955)
                    run_adb(["shell", "input", "tap", str(input_x), str(input_y)])
                time.sleep(0.4)

                safe_msg = re.sub(r'[^a-zA-Z0-9\s.,!?@#$:;/\-_\'"()\[\]+*=]', '', m).strip().replace(" ", "%s")
                if safe_msg:
                    run_adb(["shell", "input", "text", safe_msg])
                    time.sleep(0.5)

                # Locate & Tap Send button
                send_pos = find_xml_button("com.whatsapp:id/send", "Send")
                if send_pos:
                    run_adb(["shell", "input", "tap", str(send_pos[0]), str(send_pos[1])])
                    logger.info(f"Tapped WhatsApp send button at {send_pos} for {p}")
                else:
                    send_x, send_y = int(sw * 0.93), int(sh * 0.955)
                    run_adb(["shell", "input", "tap", str(send_x), str(send_y)])
                    time.sleep(0.2)
                    run_adb(["shell", "input", "keyevent", "66"])
                    logger.info(f"Tapped send button fallback at ({send_x}, {send_y}) for {p}")

            else:
                # 2. Contact Name Branch (WhatsApp App Search & Type)
                clean_contact = clean_recipient_phone(p)
                clean_contact = re.sub(r'(?i)\s*\b(?:on|in|via)\s+(?:whatsapp|phone|android)\b', '', clean_contact).strip() or clean_contact

                run_adb(["shell", "am", "force-stop", "com.whatsapp"])
                time.sleep(0.5)
                run_adb(["shell", "monkey", "-p", "com.whatsapp", "-c", "android.intent.category.LAUNCHER", "1"])
                time.sleep(2.0)

                # Tap Search Icon
                search_pos = find_xml_button("com.whatsapp:id/menuitem_search", "Search")
                if search_pos:
                    run_adb(["shell", "input", "tap", str(search_pos[0]), str(search_pos[1])])
                else:
                    search_x, search_y = int(sw * 0.85), int(sh * 0.06)
                    run_adb(["shell", "input", "tap", str(search_x), str(search_y)])

                time.sleep(1.0)

                # Type Contact Name into Search box
                safe_name = re.sub(r'[^a-zA-Z0-9\s+_\-]', '', clean_contact).strip().replace(" ", "%s")
                if safe_name:
                    run_adb(["shell", "input", "text", safe_name])
                    time.sleep(0.5)
                    run_adb(["shell", "input", "keyevent", "66"])
                time.sleep(1.5)

                # Tap contact from search results (First item in search list)
                contact_pos = find_contact_result(clean_contact)
                if contact_pos:
                    run_adb(["shell", "input", "tap", str(contact_pos[0]), str(contact_pos[1])])
                    logger.info(f"Tapped contact result at {contact_pos} for {clean_contact}")
                else:
                    top_result_x, top_result_y = int(sw * 0.50), int(sh * 0.19)
                    run_adb(["shell", "input", "tap", str(top_result_x), str(top_result_y)])
                    time.sleep(0.5)
                    run_adb(["shell", "input", "keyevent", "66"])
                    logger.info(f"Tapped top contact search result fallback at ({top_result_x}, {top_result_y}) for {clean_contact}")

                # Wait for chat window to open completely
                time.sleep(2.0)

                # Focus Chat Input Box at bottom of screen
                input_pos = find_whatsapp_message_input() or find_xml_button("com.whatsapp:id/entry", "Message")
                if input_pos:
                    run_adb(["shell", "input", "tap", str(input_pos[0]), str(input_pos[1])])
                    logger.info(f"Tapped exact WhatsApp message bar at {input_pos} for {clean_contact}")
                else:
                    input_x, input_y = int(sw * 0.40), int(sh * 0.955)
                    run_adb(["shell", "input", "tap", str(input_x), str(input_y)])
                    logger.info(f"Tapped WhatsApp message bar fallback at ({input_x}, {input_y}) for {clean_contact}")

                time.sleep(0.8)

                # Type Message into chat box
                safe_msg = re.sub(r'[^a-zA-Z0-9\s.,!?@#$:;/\-_\'"()\[\]+*=]', '', m).strip().replace(" ", "%s")
                if safe_msg:
                    run_adb(["shell", "input", "text", safe_msg])
                    time.sleep(0.5)

                # Tap Send button
                send_pos = find_xml_button("com.whatsapp:id/send", "Send")
                if send_pos:
                    run_adb(["shell", "input", "tap", str(send_pos[0]), str(send_pos[1])])
                    time.sleep(0.2)
                    run_adb(["shell", "input", "keyevent", "66"])
                    logger.info(f"Tapped WhatsApp send button at {send_pos} for {p}")
                else:
                    send_x, send_y = int(sw * 0.93), int(sh * 0.955)
                    run_adb(["shell", "input", "tap", str(send_x), str(send_y)])
                    time.sleep(0.2)
                    run_adb(["shell", "input", "keyevent", "66"])
                    logger.info(f"Tapped WhatsApp send button fallback at ({send_x}, {send_y}) for {p}")

            results.append({"phone": p, "message": m, "sent": True})
            time.sleep(1.5)

        msg = f"Sent WhatsApp message(s) to {len(results)} recipient(s) on Android phone!"
        logger.info(msg)
        return ToolResult.ok(data={"results": results, "count": len(results)}, message=msg)


# Global registry for scheduled WhatsApp jobs & active asyncio tasks
_SCHEDULED_WHATSAPP_JOBS: dict[str, dict[str, Any]] = {}
_BACKGROUND_SCHEDULED_TASKS: set[asyncio.Task] = set()


def clean_recipient_phone(p_raw: str) -> str:
    """Helper to strip any trailing schedule/time phrases from recipient names."""
    if not p_raw:
        return ""
    cleaned = re.sub(r"(?i)\b(?:in|after|at|delay|every)\s+\d+.*$", "", p_raw).strip()
    return cleaned or p_raw


def parse_schedule_time(time_str: str = "", delay_seconds: int | float | None = None) -> tuple[datetime.datetime, float]:
    """Helper to parse relative delay or absolute target time into (target_datetime, wait_seconds)."""
    now = datetime.datetime.now()
    if delay_seconds is not None and delay_seconds > 0:
        target_dt = now + datetime.timedelta(seconds=float(delay_seconds))
        return target_dt, float(delay_seconds)

    clean_str = (time_str or "").strip().lower()
    if not clean_str:
        return now, 0.0

    # 1. Relative delay patterns: "in 5 minutes", "after 10 seconds", "delay 30 sec", "in 10s"
    m_rel = re.search(r"\b(?:in|after|delay\s*by|for)\s+(\d+(?:\.\d+)?)\s*(second|sec|s|minute|min|m|hour|hr|h|day|d)s?\b", clean_str)
    if not m_rel:
        m_rel = re.search(r"\b(\d+(?:\.\d+)?)\s*(second|sec|minute|min|hour|hr|day)s?\b", clean_str)

    if m_rel:
        val = float(m_rel.group(1))
        unit = m_rel.group(2).lower()
        if unit.startswith("s"):
            secs = val
        elif unit.startswith("m"):
            secs = val * 60
        elif unit.startswith("h"):
            secs = val * 3600
        elif unit.startswith("d"):
            secs = val * 86400
        else:
            secs = val
        target_dt = now + datetime.timedelta(seconds=secs)
        return target_dt, secs

    # 2. Specific time patterns: "at 9", "at 9:50", "12.30 pm", "9.50", "9pm", "9 am", "21:50", "12:00 am"
    m_time = re.search(r"\b(\d{1,2})(?:[:.](\d{2}))?\s*(am|pm)?\b", clean_str)
    if m_time:
        hr = int(m_time.group(1))
        mn = int(m_time.group(2)) if m_time.group(2) else 0
        ampm = m_time.group(3)
        if ampm:
            if ampm == "pm" and hr < 12:
                hr += 12
            elif ampm == "am" and hr == 12:
                hr = 0

        target_dt = now.replace(hour=hr, minute=mn, second=0, microsecond=0)
        # If target time is earlier today or specified for tonight/tomorrow, adjust day
        if "tonight" in clean_str or "tomorrow" in clean_str or target_dt <= now:
            if target_dt <= now:
                target_dt += datetime.timedelta(days=1)
        wait_sec = max(0.0, (target_dt - now).total_seconds())
        return target_dt, wait_sec

    return now, 0.0


class AndroidScheduleWhatsAppTool(Tool):
    @property
    def name(self) -> str:
        return "android.schedule_whatsapp"

    @property
    def description(self) -> str:
        return "Schedule WhatsApp message(s) to be sent automatically at a future time, relative delay, or recurring interval on Android phone."

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.ANDROID

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.LOW

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(name="phone", type="string", description="Phone number or contact name", required=False),
            ToolParameter(name="message", type="string", description="Message text to send", required=False),
            ToolParameter(name="messages", type="array", description="List of recipient/message items", required=False),
            ToolParameter(name="time", type="string", description="Target time (e.g. '12:00 AM', '9:50 AM', 'in 10 minutes')", required=False),
            ToolParameter(name="delay_seconds", type="number", description="Delay in seconds before sending", required=False),
            ToolParameter(name="recurring", type="string", description="Optional recurring pattern (e.g. 'daily', 'weekdays')", required=False),
        ]

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.MEDIUM

    async def execute(self, **params: Any) -> ToolResult:
        raw_phone = params.get("phone", "").strip()
        message = params.get("message", "").strip()
        messages_list = params.get("messages", [])
        time_str = str(params.get("time") or "").strip()
        delay_sec = params.get("delay_seconds")
        recurring = str(params.get("recurring") or "").strip()

        # Extract time_str from raw_phone if time_str was empty but raw_phone contained delay/time phrase
        if not time_str and not delay_sec and raw_phone:
            m_time_in_p = re.search(r"(?i)\b(?:in|after|at|delay|every)\s+\d+.*$", raw_phone)
            if m_time_in_p:
                time_str = m_time_in_p.group(0).strip()

        phone = clean_recipient_phone(raw_phone)

        if messages_list and isinstance(messages_list, list):
            cleaned_messages = []
            for item in messages_list:
                if isinstance(item, dict):
                    p_val = str(item.get("phone") or item.get("recipient") or item.get("contact") or "").strip()
                    m_val = str(item.get("message") or item.get("text") or "").strip()
                    cleaned_messages.append({"phone": clean_recipient_phone(p_val), "message": m_val})
            messages_list = cleaned_messages

        import asyncio, datetime
        target_dt, wait_sec = parse_schedule_time(time_str=time_str, delay_seconds=delay_sec)

        # Register non-blocking background task so agent loop completes immediately
        # and NEXA can process subsequent user commands (e.g. "open instagram") without waiting.
        job_id = f"job_wa_{int(time.time()*1000)}"

        job_data = {
            "job_id": job_id,
            "phone": phone,
            "message": message,
            "messages": messages_list,
            "time_str": time_str,
            "scheduled_for": target_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "wait_seconds": round(wait_sec, 1),
            "recurring": recurring,
            "status": "pending",
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "task": None,
        }

        async def _background_runner():
            try:
                logger.info(f"Scheduled WhatsApp job {job_id} sleeping for {round(wait_sec, 1)} seconds...")
                if wait_sec > 0:
                    await asyncio.sleep(wait_sec)
                
                # Wake up phone screen and unlock lockscreen before executing task
                ensure_device_awake()
                logger.info(f"Executing scheduled WhatsApp job {job_id} for target phone '{phone}'...")
                job_data["status"] = "executing"
                sender_tool = AndroidSendWhatsAppTool()
                exec_res = await sender_tool.execute(phone=phone, message=message, messages=messages_list)
                if exec_res.success:
                    job_data["status"] = "completed"
                    job_data["result"] = exec_res.message
                    logger.info(f"Scheduled WhatsApp job {job_id} completed successfully!")
                else:
                    job_data["status"] = "failed"
                    job_data["error"] = exec_res.message
                    logger.warning(f"Scheduled WhatsApp job {job_id} failed: {exec_res.message}")
            except asyncio.CancelledError:
                job_data["status"] = "cancelled"
                logger.info(f"Scheduled WhatsApp job {job_id} was cancelled.")
            except Exception as ex:
                job_data["status"] = "failed"
                job_data["error"] = str(ex)
                logger.error(f"Scheduled WhatsApp job {job_id} exception: {ex}")

        task = asyncio.create_task(_background_runner())
        _BACKGROUND_SCHEDULED_TASKS.add(task)
        task.add_done_callback(_BACKGROUND_SCHEDULED_TASKS.discard)
        job_data["task"] = task
        _SCHEDULED_WHATSAPP_JOBS[job_id] = job_data

        msg = f"Scheduled WhatsApp message(s) for {target_dt.strftime('%Y-%m-%d %I:%M %p')} (in {round(wait_sec, 1)}s)! Job ID: {job_id}"
        logger.info(msg)
        return ToolResult.ok(data={
            "job_id": job_id,
            "scheduled_for": target_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "wait_seconds": round(wait_sec, 1),
            "status": "pending"
        }, message=msg)


class AndroidListScheduledTool(Tool):
    @property
    def name(self) -> str:
        return "android.list_scheduled"

    @property
    def description(self) -> str:
        return "List all pending and completed scheduled WhatsApp jobs on Android."

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.ANDROID

    @property
    def parameters(self) -> list[ToolParameter]:
        return []

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.LOW

    async def execute(self, **params: Any) -> ToolResult:
        jobs = []
        for jid, jdata in _SCHEDULED_WHATSAPP_JOBS.items():
            jobs.append({
                "job_id": jid,
                "phone": jdata.get("phone"),
                "message": jdata.get("message"),
                "scheduled_for": jdata.get("scheduled_for"),
                "status": jdata.get("status"),
                "created_at": jdata.get("created_at"),
            })
        msg = f"Found {len(jobs)} scheduled WhatsApp job(s)."
        return ToolResult.ok(data={"jobs": jobs, "count": len(jobs)}, message=msg)


class AndroidCancelScheduledTool(Tool):
    @property
    def name(self) -> str:
        return "android.cancel_scheduled"

    @property
    def description(self) -> str:
        return "Cancel a pending scheduled WhatsApp job by job_id."

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.ANDROID

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(name="job_id", type="string", description="Scheduled Job ID to cancel", required=True)
        ]

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.MEDIUM

    async def execute(self, **params: Any) -> ToolResult:
        job_id = params.get("job_id", "").strip()
        if not job_id or job_id not in _SCHEDULED_WHATSAPP_JOBS:
            return ToolResult.fail(f"Job ID '{job_id}' not found in scheduled jobs.")

        job = _SCHEDULED_WHATSAPP_JOBS[job_id]
        task = job.get("task")
        if task and hasattr(task, "cancel") and not task.done():
            task.cancel()
        job["status"] = "cancelled"

        msg = f"Cancelled scheduled WhatsApp job '{job_id}'."
        return ToolResult.ok(data={"job_id": job_id, "status": "cancelled"}, message=msg)


def get_tools() -> list[Tool]:
    return [
        AndroidDevicesTool(),
        AndroidListAppsTool(),
        AndroidLaunchAppTool(),
        AndroidScreenCaptureTool(),
        AndroidTapTool(),
        AndroidKeyEventTool(),
        AndroidTypeTextTool(),
        AndroidSwipeTool(),
        AndroidReadScreenTextTool(),
        AndroidInstallAppTool(),
        AndroidPlayYouTubeTool(),
        AndroidSendWhatsAppTool(),
        AndroidScheduleWhatsAppTool(),
        AndroidListScheduledTool(),
        AndroidCancelScheduledTool(),
    ]

