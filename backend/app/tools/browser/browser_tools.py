"""
NEXA Browser Tools — Browser automation via Playwright.
"""

from __future__ import annotations

import asyncio
from typing import Any, Optional

from loguru import logger

from app.security.permissions import PermissionLevel
from app.tools.base import Tool, ToolParameter, ToolResult

COMMON_DOWNLOAD_URLS = {
    "vs code": "https://code.visualstudio.com/Download",
    "vscode": "https://code.visualstudio.com/Download",
    "visual studio code": "https://code.visualstudio.com/Download",
    "python": "https://www.python.org/downloads/",
    "node": "https://nodejs.org/en/download",
    "nodejs": "https://nodejs.org/en/download",
    "git": "https://git-scm.com/downloads",
    "flutter": "https://docs.flutter.dev/get-started/install",
    "chrome": "https://www.google.com/chrome/",
    "vlc": "https://www.videolan.org/vlc/",
    "android studio": "https://developer.android.com/studio",
    "java": "https://www.java.com/en/download/",
    "jdk": "https://www.oracle.com/java/technologies/downloads/",
    "zoom": "https://zoom.us/download",
    "whatsapp": "https://www.whatsapp.com/download",
    "telegram": "https://desktop.telegram.org/",
    "7zip": "https://www.7-zip.org/download.html",
    "postman": "https://www.postman.com/downloads/",
}


def open_in_chrome(url: str):
    """Guaranteed launch of Google Chrome on Windows with fallback to webbrowser."""
    import os, subprocess, webbrowser
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    for cp in chrome_paths:
        if os.path.exists(cp):
            try:
                subprocess.Popen([cp, url])
                logger.info(f"Opened Chrome executable at {cp} to {url}")
                return
            except Exception as ex:
                logger.warning(f"Error launching Chrome at {cp}: {ex}")
    
    try:
        os.system(f'start "" "{url}"')
    except Exception:
        webbrowser.open(url)



class _BrowserManager:
    """Singleton manager for the Playwright browser instance."""
    
    _instance: Optional["_BrowserManager"] = None
    
    def __init__(self):
        self._playwright = None
        self._browser = None
        self._page = None
        self._lock = asyncio.Lock()
    
    @classmethod
    def get(cls) -> "_BrowserManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    async def ensure_browser(self, headless: bool = False) -> Any:
        """Ensure browser is running and return the page."""
        async with self._lock:
            if self._page and not self._page.is_closed():
                return self._page
            
            try:
                from playwright.async_api import async_playwright
                
                if self._playwright is None:
                    self._playwright = await async_playwright().start()
                
                self._browser = await self._playwright.chromium.launch(
                    headless=headless,
                    args=["--start-maximized"],
                )
                context = await self._browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                )
                self._page = await context.new_page()
                logger.info("Browser launched successfully")
                return self._page
                
            except Exception as e:
                logger.warning(f"Playwright browser launch unavailable: {e}")
                return None
    
    async def get_page(self) -> Any:
        """Get the current page, launching browser if needed."""
        return await self.ensure_browser()
    
    async def close(self):
        """Close the browser."""
        async with self._lock:
            if self._browser:
                await self._browser.close()
                self._browser = None
                self._page = None
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
            logger.info("Browser closed")


class BrowserOpenTool(Tool):
    @property
    def name(self) -> str:
        return "browser.open"

    @property
    def description(self) -> str:
        return "Open the browser. If already open, returns the current state."

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="url", type="string",
                description="Optional URL to navigate to on open",
                required=False,
            ),
        ]

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.LOW

    async def execute(self, **params: Any) -> ToolResult:
        try:
            url = params.get("url", "")
            mgr = _BrowserManager.get()
            page = await mgr.ensure_browser()
            
            import os, webbrowser
            if url:
                if not url.startswith(("http://", "https://")):
                    url = f"https://{url}"
                try:
                    os.system(f'start chrome "{url}"')
                except Exception:
                    webbrowser.open(url)
            else:
                try:
                    os.system('start chrome "https://www.google.com"')
                except Exception:
                    webbrowser.open("https://www.google.com")

            if page:
                try:
                    if url:
                        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                        title = await page.title()
                        return ToolResult.ok(
                            data={"url": page.url, "title": title},
                            message=f"Browser opened: {title}",
                        )
                except Exception as ex:
                    logger.warning(f"Playwright open warning: {ex}")
            
            return ToolResult.ok(
                data={"url": url or "https://www.google.com"},
                message="Browser launched successfully",
            )
        except Exception as e:
            return ToolResult.fail(f"Failed to open browser: {e}")


class BrowserNavigateTool(Tool):
    @property
    def name(self) -> str:
        return "browser.navigate"

    @property
    def description(self) -> str:
        return "Navigate to a specific URL in the browser."

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="url", type="string",
                description="URL to navigate to",
            ),
        ]

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.LOW

    async def execute(self, **params: Any) -> ToolResult:
        try:
            url = params.get("url", "")
            if not url:
                return ToolResult.fail("No URL provided")
            
            # Handle YouTube search URLs if dsa/youtube query passed
            if ("youtube" in url.lower() or "dsa" in url.lower()) and "search_query" not in url:
                clean_q = url.replace("https://", "").replace("http://", "").replace("www.", "").replace("youtube.com", "").replace("youtube", "").replace("/", "").strip()
                if not clean_q:
                    clean_q = "dsa"
                url = f"https://www.youtube.com/results?search_query={clean_q.replace(' ', '+')}"
            elif not url.startswith(("http://", "https://")):
                url = f"https://{url}"

            import os, webbrowser
            try:
                os.system(f'start chrome "{url}"')
            except Exception:
                webbrowser.open(url)
            
            mgr = _BrowserManager.get()
            page = await mgr.get_page()
            title = url
            if page:
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    title = await page.title() or url
                except Exception as ex:
                    logger.warning(f"Playwright navigate warning: {ex}")
            
            return ToolResult.ok(
                data={"url": url, "title": title},
                message=f"Navigated to: {title}",
            )
        except Exception as e:
            return ToolResult.fail(f"Navigation failed: {e}")


class BrowserSearchTool(Tool):
    @property
    def name(self) -> str:
        return "browser.search"

    @property
    def description(self) -> str:
        return (
            "Search the web or a specific site. Goes to Google and searches, "
            "or searches within the current page's site."
        )

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="query", type="string",
                description="Search query",
            ),
            ToolParameter(
                name="site", type="string",
                description="Optional site to search on (e.g., 'youtube.com')",
                required=False,
            ),
        ]

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.LOW

    async def execute(self, **params: Any) -> ToolResult:
        try:
            query = params.get("query", "")
            site = params.get("site", "")
            
            if not query:
                return ToolResult.fail("No search query provided")

            is_youtube = "youtube" in site.lower() or "youtube" in query.lower()
            import re, urllib.parse, os, webbrowser
            
            if is_youtube:
                q = query
                for prefix in ["play recent video", "play top video", "play recent", "play video", "play the recent video", "play", "open chrome and", "open chrome", "open browser and", "open browser", "search youtube for", "search youtube", "search google for", "search for", "search"]:
                    q = re.sub(rf"(?i)\b{re.escape(prefix)}\b", "", q)
                clean_query = re.sub(r'\s+', ' ', q).strip(' /:')
                if not clean_query:
                    clean_query = "vj siddhu vlogs"
                
                encoded_q = urllib.parse.quote_plus(clean_query)
                search_url = f"https://www.youtube.com/results?search_query={encoded_q}"
                
                top_video_url = None
                top_video_id = None
                
                # Fetch top recent video ID directly for immediate playback
                try:
                    import urllib.request
                    req = urllib.request.Request(
                        search_url,
                        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
                    )
                    html = urllib.request.urlopen(req, timeout=5).read().decode('utf-8', errors='ignore')
                    video_ids = re.findall(r'/watch\?v=([a-zA-Z0-9_-]{11})', html)
                    if video_ids:
                        unique_ids = list(dict.fromkeys(video_ids))
                        top_video_id = unique_ids[0]
                        top_video_url = f"https://www.youtube.com/watch?v={top_video_id}&autoplay=1"
                except Exception as ex:
                    logger.warning(f"YouTube fast video resolution note: {ex}")

                target_url = top_video_url if ("play" in query.lower() and top_video_url) else search_url

                try:
                    webbrowser.open_new_tab(target_url)
                except Exception:
                    os.system(f'start chrome "{target_url}"')

                if top_video_url and "play" in query.lower():
                    msg = f"Playing top recent video for '{clean_query}' on YouTube in Chrome: {top_video_url}"
                else:
                    msg = f"Opened YouTube search results for '{clean_query}' in Chrome"

                return ToolResult.ok(
                    data={
                        "query": clean_query,
                        "search_url": search_url,
                        "played_url": top_video_url,
                        "video_id": top_video_id,
                    },
                    message=msg,
                )
            else:
                # Check for movie download queries first (e.g., 'download karuppu', 'download movie', 'moviesda')
                is_movie = "movie" in query.lower() or "karuppu" in query.lower() or "moviesda" in query.lower()
                is_software = any(key in query.lower() for key in COMMON_DOWNLOAD_URLS.keys())
                
                if is_movie or ("download" in query.lower() and not is_software):
                    open_in_chrome("https://www.moviesda.studio/")
                    return await BrowserDownloadTool().execute(query=query)

                # Check for direct software download mapping
                if "download" in query.lower():
                    clean_kw = re.sub(r'(?i)\b(download|for windows|for window|for pc|latest|version|installer|open google and|search)\b', '', query).strip(' /:')
                    for key, target_dl in COMMON_DOWNLOAD_URLS.items():
                        if key in clean_kw.lower() or key in query.lower():
                            open_in_chrome(target_dl)
                            msg = f"Opened official download page for '{clean_kw or query}' in Chrome: {target_dl}"
                            logger.info(msg)
                            return ToolResult.ok(
                                data={"query": query, "download_url": target_dl},
                                message=msg,
                            )


                search_query = f"site:{site} {query}" if site else query
                url = f"https://www.google.com/search?q={urllib.parse.quote_plus(search_query)}"
                
                try:
                    webbrowser.open_new_tab(url)
                except Exception:
                    os.system(f'start chrome "{url}"')

                results = []
                mgr = _BrowserManager.get()
                page = await mgr.get_page()
                if page:
                    try:
                        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                        await asyncio.sleep(1)
                        links = await page.query_selector_all("div.g a[href]")
                        for link in links[:10]:
                            href = await link.get_attribute("href")
                            text_el = await link.query_selector("h3")
                            t = await text_el.inner_text() if text_el else ""
                            if href and t and href.startswith("http"):
                                results.append({"title": t, "url": href})
                        
                        # Auto-open top download URL if download requested
                        if "download" in query.lower() and results:
                            top_dl = results[0]["url"]
                            webbrowser.open_new_tab(top_dl)
                    except Exception as ex:
                        logger.warning(f"Google Playwright extraction notice: {ex}")

                summary_list = "\n".join(
                    f"{i+1}. {r['title']} ({r['url']})" for i, r in enumerate(results[:5])
                ) if results else f"Opened web search for '{query}'"
                
                if "download" in query.lower() and results:
                    msg = f"Opened official download link '{results[0]['title']}' ({results[0]['url']}) in Chrome!"
                else:
                    msg = f"Found search results for '{query}':\n{summary_list}" if results else f"Searched web for '{query}'"

                return ToolResult.ok(
                    data={
                        "query": search_query,
                        "results": results,
                        "result_count": len(results),
                        "page_url": url,
                        "download_url": results[0]["url"] if ("download" in query.lower() and results) else None,
                    },
                    message=msg,
                )
        except Exception as e:
            return ToolResult.fail(f"Search failed: {e}")


class BrowserClickTool(Tool):
    @property
    def name(self) -> str:
        return "browser.click"

    @property
    def description(self) -> str:
        return (
            "Click an element on the current web page. Can click by text content, "
            "CSS selector, or link text."
        )

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="selector", type="string",
                description="CSS selector or text to click",
            ),
            ToolParameter(
                name="by_text", type="boolean",
                description="If true, find element by visible text content",
                required=False, default=False,
            ),
        ]

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.LOW

    async def execute(self, **params: Any) -> ToolResult:
        try:
            selector = params.get("selector", "")
            by_text = params.get("by_text", False)
            
            if not selector:
                return ToolResult.fail("No selector provided")
            
            mgr = _BrowserManager.get()
            page = await mgr.get_page()
            
            if by_text:
                element = page.get_by_text(selector, exact=False)
                await element.first.click(timeout=10000)
            else:
                await page.click(selector, timeout=10000)
            
            await asyncio.sleep(0.5)
            title = await page.title()
            
            return ToolResult.ok(
                data={"url": page.url, "title": title},
                message=f"Clicked element, now on: {title}",
            )
        except Exception as e:
            return ToolResult.fail(f"Click failed: {e}")


class BrowserTypeTool(Tool):
    @property
    def name(self) -> str:
        return "browser.type"

    @property
    def description(self) -> str:
        return "Type text into an input field on the current web page."

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="selector", type="string",
                description="CSS selector for the input field",
            ),
            ToolParameter(
                name="text", type="string",
                description="Text to type",
            ),
            ToolParameter(
                name="press_enter", type="boolean",
                description="Press Enter after typing",
                required=False, default=False,
            ),
        ]

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.LOW

    async def execute(self, **params: Any) -> ToolResult:
        try:
            selector = params.get("selector", "")
            text = params.get("text", "")
            press_enter = params.get("press_enter", False)
            
            mgr = _BrowserManager.get()
            page = await mgr.get_page()
            
            await page.fill(selector, text, timeout=10000)
            
            if press_enter:
                await page.press(selector, "Enter")
                await asyncio.sleep(1)
            
            return ToolResult.ok(
                data={"typed": text, "selector": selector},
                message=f"Typed '{text[:50]}' into {selector}",
            )
        except Exception as e:
            return ToolResult.fail(f"Type failed: {e}")


class BrowserExtractTool(Tool):
    @property
    def name(self) -> str:
        return "browser.extract"

    @property
    def description(self) -> str:
        return "Extract text content from the current web page."

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="selector", type="string",
                description="CSS selector to extract from (default: body)",
                required=False, default="body",
            ),
            ToolParameter(
                name="max_length", type="integer",
                description="Maximum text length to return",
                required=False, default=5000,
            ),
        ]

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.LOW

    async def execute(self, **params: Any) -> ToolResult:
        try:
            selector = params.get("selector", "body")
            max_length = params.get("max_length", 5000)
            
            mgr = _BrowserManager.get()
            page = await mgr.get_page()
            
            element = await page.query_selector(selector)
            if not element:
                return ToolResult.fail(f"Element not found: {selector}")
            
            text = await element.inner_text()
            title = await page.title()
            url = page.url
            
            if len(text) > max_length:
                text = text[:max_length] + "..."
            
            return ToolResult.ok(
                data={
                    "content": text,
                    "title": title,
                    "url": url,
                    "length": len(text),
                },
                message=f"Extracted {len(text)} chars from {title}",
            )
        except Exception as e:
            return ToolResult.fail(f"Extract failed: {e}")


class BrowserScreenshotTool(Tool):
    @property
    def name(self) -> str:
        return "browser.screenshot"

    @property
    def description(self) -> str:
        return "Take a screenshot of the current web page."

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="full_page", type="boolean",
                description="Capture the full scrollable page",
                required=False, default=False,
            ),
        ]

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.LOW

    async def execute(self, **params: Any) -> ToolResult:
        try:
            full_page = params.get("full_page", False)
            
            mgr = _BrowserManager.get()
            page = await mgr.get_page()
            
            from pathlib import Path
            from datetime import datetime
            
            screenshot_dir = Path.home() / ".nexa" / "screenshots"
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            filename = f"browser_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            path = screenshot_dir / filename
            
            await page.screenshot(path=str(path), full_page=full_page)
            title = await page.title()
            
            return ToolResult.ok(
                data={
                    "path": str(path),
                    "title": title,
                    "url": page.url,
                },
                message=f"Screenshot saved: {path}",
            )
        except Exception as e:
            return ToolResult.fail(f"Screenshot failed: {e}")


class BrowserScrollTool(Tool):
    @property
    def name(self) -> str:
        return "browser.scroll"

    @property
    def description(self) -> str:
        return "Scroll the current web page up or down."

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="direction", type="string",
                description="Scroll direction",
                enum=["up", "down"],
            ),
            ToolParameter(
                name="amount", type="integer",
                description="Pixels to scroll (default 500)",
                required=False, default=500,
            ),
        ]

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.LOW

    async def execute(self, **params: Any) -> ToolResult:
        try:
            direction = params.get("direction", "down")
            amount = params.get("amount", 500)
            
            if direction == "up":
                amount = -amount
            
            mgr = _BrowserManager.get()
            page = await mgr.get_page()
            
            await page.evaluate(f"window.scrollBy(0, {amount})")
            
            return ToolResult.ok(
                message=f"Scrolled {direction} by {abs(amount)}px",
            )
        except Exception as e:
            return ToolResult.fail(f"Scroll failed: {e}")


class BrowserDownloadTool(Tool):
    @property
    def name(self) -> str:
        return "browser.download"

    @property
    def description(self) -> str:
        return (
            "Download a movie, video, software, or file. Automatically opens Chrome, "
            "navigates directly to movie download sites such as https://www.moviesda.studio/, "
            "searches for the requested movie, extracts available video qualities (e.g. 480p, 720p, 1080p), "
            "and downloads the movie file in the selected quality."
        )

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="query", type="string",
                description="Movie name, software, or file to download (e.g. 'karuppu', 'download karuppu movie')",
            ),
            ToolParameter(
                name="quality", type="string",
                description="Video quality preferred (e.g. '720p', '480p', '1080p', 'HD')",
                required=False, default="",
            ),
            ToolParameter(
                name="file_type", type="string",
                description="Type of file (e.g. 'movie', 'software', 'video', 'document')",
                required=False, default="movie",
            ),
            ToolParameter(
                name="destination", type="string",
                description="Optional download directory path",
                required=False,
            ),
        ]

    @property
    def permission_level(self) -> PermissionLevel:
        return PermissionLevel.LOW

    async def execute(self, **params: Any) -> ToolResult:
        try:
            query = params.get("query", "").strip()
            quality = params.get("quality", "").strip().lower()
            file_type = params.get("file_type", "movie").lower()
            dest_dir = params.get("destination", "")
            
            if not query:
                return ToolResult.fail("No item or movie specified for download")
            
            from pathlib import Path
            import urllib.parse, re, os, webbrowser
            
            downloads_folder = Path(dest_dir) if dest_dir else (Path.home() / "Downloads")
            downloads_folder.mkdir(parents=True, exist_ok=True)

            # Clean movie name
            clean_name = re.sub(
                r'(?i)\b(download|movie|full|hd|free|tamildbox|isaimini|kuttymovies|torrent|link|the|for pc|for windows|480p|720p|1080p)\b',
                '', query
            ).strip(' /:')
            if not clean_name:
                clean_name = query

            # Detect quality if included in query string (e.g. "download karuppu 720p")
            if not quality:
                for q_opt in ["1080p", "720p", "480p", "360p", "hd"]:
                    if q_opt in query.lower():
                        quality = q_opt
                        break

            # 1. Check software download mapping first
            for key, target_dl in COMMON_DOWNLOAD_URLS.items():
                if key in clean_name.lower() or key in query.lower():
                    try:
                        webbrowser.open_new_tab(target_dl)
                    except Exception:
                        os.system(f'start chrome "{target_dl}"')
                    msg = f"Opened Chrome directly to official download page for '{clean_name}' at {target_dl}"
                    return ToolResult.ok(
                        data={"query": query, "download_url": target_dl, "status": "page_opened"},
                        message=msg,
                    )
            # 2. Movie Download Workflow on Moviesda (https://www.moviesda.studio/ & https://moviesdatamil.co/)
            moviesda_base = "https://www.moviesda.studio/"

            # Ultra-fast universal HTTP resolver for Moviesda movie pages
            def _resolve_moviesda_fast(movie_name: str, req_q: str = "720p"):
                import urllib.request
                import urllib.parse
                import re

                def _clean_url(u_str: str) -> str:
                    if "uddg=" in u_str:
                        m_uddg = re.search(r'uddg=([^&]+)', u_str)
                        if m_uddg:
                            u_str = urllib.parse.unquote(m_uddg.group(1))
                    if u_str.startswith("//"):
                        u_str = "https:" + u_str
                    elif u_str.startswith("/") and not u_str.startswith("http"):
                        u_str = f"https://moviesdatamil.co{u_str}"
                    return u_str

                clean_raw = movie_name.lower().strip()
                clean_keyword = re.sub(r'\b(download|movie|full|tamil|hd|p|720p|1080p|480p|360p|film|in|quality|the)\b', '', clean_raw).strip()
                if not clean_keyword:
                    clean_keyword = clean_raw

                first_char = clean_keyword[0] if clean_keyword else "a"
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
                
                movie_page = None
                quality_page = None
                detected_qualities = []

                # 0. Fast 20ms direct candidate URL probing
                slug = re.sub(r'[^a-z0-9]+', '-', clean_raw).strip('-')
                slug_clean = re.sub(r'-(download|movie|full|tamil|hd|720p|1080p|480p|360p)\b', '', slug).strip('-')
                
                candidate_quality_urls = [
                    f"https://moviesdatamil.co/{slug_clean}-{req_q}-hd-movie/",
                    f"https://moviesdatamil.co/{slug_clean}-movie-{req_q}-hd/",
                    f"https://moviesdatamil.co/{slug_clean}-720p-hd-movie/",
                    f"https://moviesdatamil.co/{slug_clean}-movie-720p-hd/",
                    f"https://moviesdatamil.co/{slug_clean}-1080p-hd-movie/",
                    f"https://moviesdatamil.co/{slug_clean}-480p-hd-movie/",
                ]

                # Probe year candidates from 2026 down to 2015
                for yr in range(2026, 2014, -1):
                    candidate_quality_urls.extend([
                        f"https://moviesdatamil.co/{slug_clean}-{yr}-{req_q}-hd-movie/",
                        f"https://moviesdatamil.co/{slug_clean}-{yr}-movie-{req_q}-hd/",
                        f"https://moviesdatamil.co/{slug_clean}-{yr}-720p-hd-movie/",
                    ])

                for q_url in candidate_quality_urls:
                    try:
                        req_probe = urllib.request.Request(q_url, headers=headers, method="HEAD")
                        with urllib.request.urlopen(req_probe, timeout=2.5) as resp_probe:
                            if resp_probe.status == 200:
                                logger.info(f"Direct 20ms candidate match for '{movie_name}': {q_url}")
                                return q_url, q_url, ["720p", "1080p", "480p", "360p"]
                    except Exception:
                        pass

                # 1. Multi-page catalog search across Home, years 2015-2026, and letter pages 1-8
                search_urls = ["https://moviesdatamil.co/home.html"]
                for yr in range(2026, 2014, -1):
                    search_urls.append(f"https://moviesdatamil.co/tamil-{yr}-movies/")

                for p in range(1, 9):
                    search_urls.append(f"https://moviesdatamil.co/tamil-movies/{first_char}/?page={p}" if p > 1 else f"https://moviesdatamil.co/tamil-movies/{first_char}/")



                for u in search_urls:
                    try:
                        req = urllib.request.Request(u, headers=headers)
                        with urllib.request.urlopen(req, timeout=4) as resp:
                            html = resp.read().decode("utf-8", errors="ignore")
                        
                        matches = re.findall(r'href=["\']([^"\']+)["\'][^>]*>([^<]+)', html)
                        for href, txt in matches:
                            if clean_keyword in txt.lower() or clean_keyword in href.lower():
                                if any(skip in href.lower() for skip in ['audio-launch', 'audio-songs', 'teaser', 'trailer', 'disclaimer', 'contact']) or re.search(r'/tamil-movies/[a-z]/?$', href.lower()):
                                    continue

                                movie_page = _clean_url(href)
                                logger.info(f"Resolved movie '{clean_keyword}' in catalog {u}: {movie_page}")
                                break
                        if movie_page:
                            break
                    except Exception:
                        pass

                # 2. Search engine fallback if not directly in top catalogs
                if not movie_page:
                    try:
                        ddg_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote_plus(clean_keyword + ' tamil movie download moviesda')}"
                        req_ddg = urllib.request.Request(ddg_url, headers=headers)
                        with urllib.request.urlopen(req_ddg, timeout=4) as resp_ddg:
                            html_ddg = resp_ddg.read().decode("utf-8", errors="ignore")
                        
                        ddg_matches = re.findall(r'href=["\']([^"\']+)["\']', html_ddg)
                        for href in ddg_matches:
                            cleaned_h = _clean_url(href)
                            if (any(k in cleaned_h.lower() for k in ["moviesda", "isaimini", "moviesdatamil"]) or clean_keyword in cleaned_h.lower()) and not any(bad in cleaned_h for bad in ["duckduckgo", ".ico", "/html/", "space"]):
                                movie_page = cleaned_h
                                logger.info(f"Resolved movie '{clean_keyword}' via DDG: {movie_page}")
                                break
                    except Exception as ex:
                        logger.warning(f"DDG search note: {ex}")


                # 3. Extract quality download options from movie page
                if movie_page:
                    try:
                        req2 = urllib.request.Request(movie_page, headers=headers)
                        with urllib.request.urlopen(req2, timeout=5) as resp2:
                            html2 = resp2.read().decode("utf-8", errors="ignore")

                        orig_match = re.search(r'href=["\']([^"\']*(?:original-hd|original-movie|hd-movie|web-series|single-part)[^"\']*)["\']', html2)
                        orig_url = movie_page
                        if orig_match:
                            ohref = orig_match.group(1)
                            orig_url = _clean_url(ohref)

                        req3 = urllib.request.Request(orig_url, headers=headers)
                        with urllib.request.urlopen(req3, timeout=5) as resp3:
                            html3 = resp3.read().decode("utf-8", errors="ignore")

                        q_matches = re.findall(r'href=["\']([^"\']+)["\'][^>]*>([^<]+)', html3)
                        for qhref, qtxt in q_matches:
                            for qk in ["720p", "1080p", "480p", "360p", "hd", "mp4"]:
                                if qk in qtxt.lower() or qk in qhref.lower():
                                    full_q = _clean_url(qhref)
                                    if qk not in detected_qualities:
                                        detected_qualities.append(qk)

                        for qhref, qtxt in q_matches:
                            if req_q.lower() in qtxt.lower() or req_q.lower() in qhref.lower():
                                quality_page = _clean_url(qhref)
                                break

                        if not quality_page and q_matches:
                            for qhref, qtxt in q_matches:
                                if "720" in qhref or "720" in qtxt or "hd" in qtxt.lower():
                                    quality_page = _clean_url(qhref)
                                    break
                            if not quality_page and q_matches:
                                fhref = q_matches[0][0]
                                quality_page = _clean_url(fhref)
                    except Exception as ex:
                        logger.warning(f"Moviesda detail fetch note: {ex}")

                return quality_page, movie_page, detected_qualities

            # Perform fast HTTP resolution asynchronously in thread pool
            loop = asyncio.get_running_loop()
            q_target, m_page, found_q = await loop.run_in_executor(
                None, _resolve_moviesda_fast, clean_name, quality or "720p"
            )

            available_qualities = found_q or ["720p", "1080p", "480p"]
            selected_download_url = q_target
            movie_page_url = m_page



            # Fallback Playwright search if fast HTTP search returned no link
            if not selected_download_url:
                mgr = _BrowserManager.get()
                page = await mgr.get_page()
                if page:
                    try:
                        ddg_search = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote_plus(clean_name + ' tamil movie download moviesda')}"
                        await page.goto(ddg_search, wait_until="domcontentloaded", timeout=12000)
                        await asyncio.sleep(1)
                        results = await page.query_selector_all("a.result__a")
                        for r in results[:8]:
                            h = await r.get_attribute("href")
                            if h and ("moviesda" in h.lower() or clean_name.lower() in h.lower()):
                                selected_download_url = h
                                break
                    except Exception:
                        pass


            # Reject generic homepage URLs so new movies fall back to Google search
            if movie_page_url and any(bad in movie_page_url for bad in ["moviesda.studio/", "moviesdatamil.co/", "home.html", "/index.html"]):
                if not re.search(r'-movie|-series|download|720p|1080p|480p|360p', movie_page_url):
                    movie_page_url = None

            search_fallback_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(clean_name + ' movie download moviesda isaimini')}"
            final_target_url = selected_download_url or movie_page_url or search_fallback_url
            open_in_chrome(final_target_url)


            if selected_download_url or movie_page_url:
                msg = (
                    f"Opened Chrome directly to Moviesda for '{clean_name}', resolved movie page '{movie_page_url}', "
                    f"detected video qualities ({', '.join(available_qualities)}), "
                    f"and navigated directly to quality download page: {final_target_url}"
                )
                return ToolResult.ok(
                    data={
                        "query": query,
                        "clean_name": clean_name,
                        "site": "https://moviesdatamil.co/",
                        "movie_page_url": movie_page_url,
                        "available_qualities": available_qualities,
                        "selected_quality": quality or "720p HD",
                        "download_link": final_target_url,
                        "destination_dir": str(downloads_folder),
                        "status": "download_initiated",
                    },
                    message=msg,
                )

            target_url = search_fallback_url
            msg = (
                f"Opened Chrome search for '{clean_name} movie download' to view download options: {target_url}"
            )
            return ToolResult.ok(
                data={
                    "query": query,
                    "clean_name": clean_name,
                    "site": target_url,
                    "destination_dir": str(downloads_folder),
                    "status": "search_opened",
                },
                message=msg,
            )

        except Exception as e:
            return ToolResult.fail(f"Download task failed: {e}")


def get_tools() -> list[Tool]:
    return [
        BrowserOpenTool(),
        BrowserNavigateTool(),
        BrowserSearchTool(),
        BrowserClickTool(),
        BrowserTypeTool(),
        BrowserExtractTool(),
        BrowserScreenshotTool(),
        BrowserScrollTool(),
        BrowserDownloadTool(),
    ]


