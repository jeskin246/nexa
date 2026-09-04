"""
NEXA AI — Local Rule-Based Provider (Zero API Key Fallback).

Enables NEXA to work completely offline out-of-the-box without requiring
any API keys or external services.
"""

from __future__ import annotations

import json
import re
from typing import Any, Optional

from loguru import logger

from app.ai.base import LLMMessage, LLMProvider, LLMResponse, LLMToolCall


class PlanStep:
    def __init__(self, tool_name: str, parameters: dict[str, Any], description: str = ""):
        self.tool_name = tool_name
        self.parameters = parameters
        self.description = description

class Plan:
    def __init__(self, steps: list[PlanStep]):
        self.steps = steps


class LocalRuleProvider(LLMProvider):
    """
    Local rule-based fallback provider.
    
    Parses natural language requests using intent analysis rules
    and generates multi-step execution plans using NEXA's built-in tool system.
    """

    def __init__(self, model: str = "nexa-local-rules"):
        self._model = model
        logger.info(f"LocalRuleProvider initialized (Zero-key offline mode): {self._model}")

    @property
    def name(self) -> str:
        return "local_rules"

    @property
    def model(self) -> str:
        return self._model

    async def complete(
        self,
        messages: list[LLMMessage],
        tools: Optional[list[dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        user_msg = ""
        for m in reversed(messages):
            if m.role == "user":
                user_msg = m.content
                break

        summary = self._summarize_user_content(user_msg)

        return LLMResponse(
            content=summary,
            finish_reason="stop",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        )

    async def complete_structured(
        self,
        messages: list[LLMMessage],
        response_schema: dict[str, Any],
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        user_msg = ""
        for m in reversed(messages):
            if m.role == "user":
                user_msg = m.content
                break

        user_lower = user_msg.lower()

        # Check if intent analysis requested
        if "category" in response_schema.get("properties", {}):
            return {
                "intent": user_msg[:100],
                "category": self._detect_category(user_lower),
                "complexity": "moderate",
                "requires_confirmation": any(
                    k in user_lower for k in ["delete", "remove", "kill", "publish", "send"]
                ),
            }

        # Check if plan schema requested
        if "steps" in response_schema.get("properties", {}):
            steps = self._generate_rule_plan(user_msg)
            return {
                "understanding": f"Execute goal: {user_msg}",
                "steps": steps,
                "estimated_risk": "low",
            }

        # Verification schema
        if "confidence" in response_schema.get("properties", {}):
            return {
                "success": True,
                "confidence": 0.9,
                "message": "Action completed successfully",
                "suggestion": "",
            }

        return {"status": "ok", "message": "Action processed by local rule engine"}

    def _detect_category(self, text: str) -> str:
        if any(k in text for k in ["search", "find", "locate"]):
            return "search"
        if any(k in text for k in ["create", "make", "write"]):
            return "create"
        if any(k in text for k in ["delete", "remove"]):
            return "delete"
        if any(k in text for k in ["open", "launch", "browser", "youtube"]):
            return "navigate"
        return "automate"

    def _generate_rule_plan(self, text: str) -> list[dict[str, Any]]:
        # Split multi-clause compound prompts (e.g. "schedule whatsapp ... AND open instagram")
        raw_clauses = re.split(r'\b(?:and\s+then|then|;\s*|\n+)\b', text, flags=re.IGNORECASE)
        if len(raw_clauses) == 1:
            m_parts = re.split(r'\b(?=and\s+(?:open|launch|install|start))\b', text, flags=re.IGNORECASE)
            clauses = [re.sub(r'^\s*and\s+', '', p, flags=re.IGNORECASE).strip() for p in m_parts if p.strip()]
        else:
            clauses = [c.strip() for c in raw_clauses if c.strip()]

        if len(clauses) > 1:
            all_steps = []
            for c in clauses:
                sub_steps = self._generate_single_rule_plan(c)
                for s in sub_steps:
                    s["index"] = len(all_steps)
                    all_steps.append(s)
            if all_steps:
                return all_steps

        return self._generate_single_rule_plan(text)

    def _generate_single_rule_plan(self, text: str) -> list[dict[str, Any]]:
        text_lower = text.lower()
        steps = []

        # Open / Launch app intent rule (standalone or compound)
        if (text_lower.startswith("open ") or text_lower.startswith("launch ") or text_lower.startswith("start ") or "open app" in text_lower or "launch app" in text_lower) and not "whatsapp" in text_lower:
            app_name = text
            for p in ["open", "launch", "start", "app", "on android", "on phone", "in android", "in phone"]:
                app_name = re.sub(rf"(?i)\b{re.escape(p)}\b", "", app_name)
            clean_app = app_name.strip(" /:") or "notepad"

            is_android = any(k in text_lower for k in ["android", "phone", "mobile"]) or clean_app.lower() in ["instagram", "snapchat", "zomato", "swiggy", "zepto", "blinkit", "uber", "ola", "paytm", "phonepe"]
            tool_name = "android.launch_app" if is_android else "app.launch"
            desc = f"Launch '{clean_app}' app on phone" if is_android else f"Launch application: {clean_app}"

            steps.append({
                "index": 0,
                "description": desc,
                "tool_name": tool_name,
                "parameters": {"name": clean_app},
            })
            return steps

        # Install app intent rule
        if text_lower.startswith("install ") or "install app" in text_lower:
            app_name = text
            for p in ["install", "app", "the app", "on android", "on phone", "in android", "in phone", "from playstore", "from play store"]:
                app_name = re.sub(rf"(?i)\b{re.escape(p)}\b", "", app_name)
            clean_app = app_name.strip(" /:") or "telegram"
            steps.append({
                "index": 0,
                "description": f"Open Google Play Store to install '{clean_app}' on phone",
                "tool_name": "android.install_app",
                "parameters": {"name": clean_app},
            })
            return steps

        # YouTube Intent Rule (Android ADB YouTube bridge)
        # Supports: "play top video of dsa on youtube", "play recent video python tutorial", "play high view video machine learning", etc.
        has_yt = "youtube" in text_lower or ("video" in text_lower and any(k in text_lower for k in ["play", "watch", "stream"]))
        is_sharing = any(k in text_lower for k in ["share", "send", "forward"]) and ("whatsapp" in text_lower or "to " in text_lower)
        if has_yt and ("play" in text_lower or "watch" in text_lower or "video" in text_lower or "open" in text_lower or "search" in text_lower) and not is_sharing:
            is_search = "search" in text_lower and not any(k in text_lower for k in ["play", "watch"])

            # Detect filter: recent (upload date), views (most viewed/popular), relevant (top)
            yt_filter = "relevant"
            if any(k in text_lower for k in ["recent", "latest", "new", "newest"]):
                yt_filter = "recent"
            elif any(k in text_lower for k in ["high view", "highest view", "highest views", "most viewed", "most views", "most popular", "popular", "trending", "views"]):
                yt_filter = "views"
            elif any(k in text_lower for k in ["top", "best", "relevant"]):
                yt_filter = "relevant"

            yt_query = text
            strip_patterns = [
                "play", "watch", "video of", "video", "on youtube", "in youtube", "youtube",
                "on phone", "on android", "open", "search for", "search in", "search",
                "high view", "highest view", "highest views", "most viewed", "most views",
                "most popular", "popular", "trending", "recent", "latest", "newest", "new",
                "top", "best", "relevant"
            ]
            for p in strip_patterns:
                yt_query = re.sub(rf"(?i)\b{re.escape(p)}\b", "", yt_query)
            clean_query = re.sub(r'^\s*(?:for|about|search|of)\s+', '', yt_query.strip(" /:\"'"), flags=re.IGNORECASE).strip() or "lofi beats"
            action_type = "search" if is_search else "play"
            steps.append({
                "index": 0,
                "description": f"{'Search' if is_search else 'Play'} {yt_filter} YouTube video for '{clean_query}' on Android phone",
                "tool_name": "android.play_youtube",
                "parameters": {"query": clean_query, "action": action_type, "filter": yt_filter},
            })
            return steps


        # Cross-App Sharing Rule (e.g. "share vj siddhu vlogs video youtube to saritha in whatsapp", "share link of dsa to saritha in whatsapp")
        if ("share" in text_lower or "send" in text_lower or "forward" in text_lower) and ("link" in text_lower or "youtube" in text_lower or "video" in text_lower or "vlogs" in text_lower or "vlog" in text_lower or "http://" in text_lower or "https://" in text_lower) and ("whatsapp" in text_lower or "to " in text_lower):
            # 1. Direct URL in prompt (e.g. "share link https://... to John")
            direct_url_match = re.search(r'(https?://[^\s]+)', text)
            direct_url = direct_url_match.group(1) if direct_url_match else ""

            # 2. Extract recipient contact
            rec_match = re.search(r'\bto\s+([a-zA-Z0-9_\s]+?)(?:\s+in\s+whatsapp|\s+on\s+whatsapp|\s+via\s+whatsapp|\s+whatsapp|\s+at\s+\d+|\s+in\s+\d+|\s*$)', text, re.IGNORECASE)
            recipient = rec_match.group(1).strip() if rec_match else "saritha"
            if recipient.lower() in ["whatsapp", "youtube", "video", "vlogs", "vlog", "link"]:
                recipient = "saritha"

            # 3. Extract time if scheduled
            is_scheduled = False
            sched_time = ""
            time_match = re.search(r'\b(at\s+\d{1,2}(?:[:.]\d{2})?\s*(?:am|pm)?|in\s+\d+\s*(?:sec|seconds|min|minutes|hours))\b', text, re.IGNORECASE)
            if time_match:
                is_scheduled = True
                sched_time = time_match.group(1).strip()

            # 4. Filter for YouTube links (recent, views, top)
            sp_param = ""
            if any(k in text_lower for k in ["recent", "latest", "new", "newest"]):
                sp_param = "&sp=EgIIAQ%253D%253D"
            elif any(k in text_lower for k in ["high view", "highest view", "highest views", "most viewed", "most views", "popular", "most popular", "trending", "views"]):
                sp_param = "&sp=CAM%253D"

            # 5. Extract topic
            yt_query = text
            if direct_url:
                yt_query = yt_query.replace(direct_url, "")
            strip_p = [
                "share", "send", "forward", "link", "url", "video of", "video", "youtube",
                "in whatsapp", "on whatsapp", "via whatsapp", "whatsapp",
                "high view", "highest view", "most viewed", "recent", "latest", "top"
            ]
            for p in strip_p:
                yt_query = re.sub(rf"(?i)\b{re.escape(p)}\b", "", yt_query)
            if recipient:
                yt_query = re.sub(rf"(?i)\bto\s+{re.escape(recipient)}\b", "", yt_query)
            if time_match:
                yt_query = re.sub(rf"(?i){re.escape(time_match.group(0))}", "", yt_query)

            clean_topic = re.sub(r'^\s*(?:of|about|link|url|for)\s+', '', yt_query.strip(" /:\"'"), flags=re.IGNORECASE).strip() or (direct_url if direct_url else "vj siddhu vlogs")

            # 6. Resolve final link
            if direct_url:
                video_url = direct_url
                message_body = f"Here is the link: {video_url}"
            else:
                video_url = ""
                try:
                    import urllib.parse, urllib.request
                    search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(clean_topic)}{sp_param}"
                    req = urllib.request.Request(search_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                    with urllib.request.urlopen(req, timeout=3) as resp:
                        html = resp.read().decode("utf-8", errors="ignore")
                        vids = re.findall(r'(?:"videoId":\s*"|/watch\?v=)([a-zA-Z0-9_-]{11})', html)
                        if vids:
                            video_url = f"https://www.youtube.com/watch?v={vids[0]}"
                except Exception:
                    pass

                if not video_url:
                    video_url = f"https://www.youtube.com/results?search_query={clean_topic.replace(' ', '+')}"

                message_body = f"Check out this YouTube video '{clean_topic}': {video_url}"

            tool_name = "android.schedule_whatsapp" if is_scheduled else "android.send_whatsapp"
            params = {"phone": recipient, "message": message_body}
            if is_scheduled:
                params["time"] = sched_time

            steps.append({
                "index": 0,
                "description": f"{'Schedule' if is_scheduled else 'Send'} link '{clean_topic}' to '{recipient}' on WhatsApp",
                "tool_name": tool_name,
                "parameters": params,
            })
            return steps

        # Universal Pipeline 1: Screenshot -> Send to WhatsApp
        if ("screenshot" in text_lower or "screen capture" in text_lower) and ("send" in text_lower or "share" in text_lower or "whatsapp" in text_lower):
            rec_match = re.search(r'\bto\s+([a-zA-Z0-9_\s]+?)(?:\s+in\s+whatsapp|\s+on\s+whatsapp|\s+via\s+whatsapp|\s+whatsapp|\s*$)', text, re.IGNORECASE)
            recipient = rec_match.group(1).strip() if rec_match else "saritha"
            if recipient.lower() in ["whatsapp", "screenshot", "screen"]:
                recipient = "saritha"

            steps.append({
                "index": 0,
                "description": "Capture Android phone screen",
                "tool_name": "android.screenshot",
                "parameters": {},
            })
            steps.append({
                "index": 1,
                "description": f"Send screenshot image to '{recipient}' on WhatsApp",
                "tool_name": "android.send_whatsapp",
                "parameters": {"phone": recipient, "message": "Here is the screenshot from my phone", "send_screenshot": True},
            })
            return steps

        # Universal Pipeline 2: Google Search -> Send Link to WhatsApp
        if ("google" in text_lower or "search" in text_lower) and ("send" in text_lower or "share" in text_lower or "link" in text_lower) and ("whatsapp" in text_lower or "to " in text_lower) and not "youtube" in text_lower:
            rec_match = re.search(r'\bto\s+([a-zA-Z0-9_\s]+?)(?:\s+in\s+whatsapp|\s+on\s+whatsapp|\s+via\s+whatsapp|\s+whatsapp|\s*$)', text, re.IGNORECASE)
            recipient = rec_match.group(1).strip() if rec_match else "saritha"
            if recipient.lower() in ["whatsapp", "google", "search", "link"]:
                recipient = "saritha"

            q_text = text
            for p in ["search", "google", "send", "share", "link", "in whatsapp", "on whatsapp", "via whatsapp", "whatsapp", "and", "then", "on"]:
                q_text = re.sub(rf"(?i)\b{re.escape(p)}\b", "", q_text)
            if recipient:
                q_text = re.sub(rf"(?i)\bto\s+{re.escape(recipient)}\b", "", q_text)

            clean_q = re.sub(r'^\s*(?:for|about|link)\s+', '', q_text.strip(" /:"), flags=re.IGNORECASE).strip() or "python tutorials"
            import urllib.parse
            google_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(clean_q)}"

            steps.append({
                "index": 0,
                "description": f"Send Google search link for '{clean_q}' to '{recipient}' on WhatsApp",
                "tool_name": "android.send_whatsapp",
                "parameters": {"phone": recipient, "message": f"Google Search results for '{clean_q}': {google_url}"},
            })
            return steps

        # Universal Pipeline 3: Play Store App Link -> Send to WhatsApp
        if ("playstore" in text_lower or "play store" in text_lower or "app link" in text_lower) and ("send" in text_lower or "share" in text_lower):
            rec_match = re.search(r'\bto\s+([a-zA-Z0-9_\s]+?)(?:\s+in\s+whatsapp|\s+on\s+whatsapp|\s+via\s+whatsapp|\s+whatsapp|\s*$)', text, re.IGNORECASE)
            recipient = rec_match.group(1).strip() if rec_match else "saritha"
            if recipient.lower() in ["whatsapp", "playstore", "play store", "app", "link"]:
                recipient = "saritha"

            app_text = text
            for p in ["share", "send", "playstore", "play store", "app link", "link", "in whatsapp", "on whatsapp", "via whatsapp", "whatsapp"]:
                app_text = re.sub(rf"(?i)\b{re.escape(p)}\b", "", app_text)
            if recipient:
                app_text = re.sub(rf"(?i)\bto\s+{re.escape(recipient)}\b", "", app_text)

            clean_app = re.sub(r'^\s*(?:for|of|link)\s+', '', app_text.strip(" /:"), flags=re.IGNORECASE).strip() or "telegram"
            import urllib.parse
            play_url = f"https://play.google.com/store/search?q={urllib.parse.quote_plus(clean_app)}&c=apps"

            steps.append({
                "index": 0,
                "description": f"Send Google Play Store link for '{clean_app}' to '{recipient}' on WhatsApp",
                "tool_name": "android.send_whatsapp",
                "parameters": {"phone": recipient, "message": f"Check out '{clean_app}' on Google Play Store: {play_url}"},
            })
            return steps

        # Scheduled WhatsApp Management Rules
        if "scheduled" in text_lower and any(k in text_lower for k in ["list", "show", "get", "view", "see"]):
            steps.append({
                "index": 0,
                "description": "List all scheduled WhatsApp messages",
                "tool_name": "android.list_scheduled",
                "parameters": {},
            })
            return steps
        elif "scheduled" in text_lower and any(k in text_lower for k in ["cancel", "delete", "remove", "stop"]):
            job_match = re.search(r'\b(job_wa_\d+|sched_[a-zA-Z0-9]+)\b', text, re.IGNORECASE)
            job_id = job_match.group(1) if job_match else ""
            steps.append({
                "index": 0,
                "description": f"Cancel scheduled WhatsApp job '{job_id}'",
                "tool_name": "android.cancel_scheduled",
                "parameters": {"job_id": job_id},
            })
            return steps

        # Standalone Screen & UI Automation Rules (Swipe, Screenshot, Read Screen)
        if "swipe" in text_lower or "scroll" in text_lower:
            direction = "down" if "down" in text_lower else ("up" if "up" in text_lower else ("left" if "left" in text_lower else "right"))
            steps.append({
                "index": 0,
                "description": f"Swipe {direction} on phone screen",
                "tool_name": "android.swipe",
                "parameters": {"direction": direction},
            })
            return steps

        if "read screen" in text_lower or "read text" in text_lower or "text on screen" in text_lower:
            steps.append({
                "index": 0,
                "description": "Read all visible text elements on Android screen",
                "tool_name": "android.read_screen_text",
                "parameters": {},
            })
            return steps

        if ("screenshot" in text_lower or "capture screen" in text_lower) and any(k in text_lower for k in ["android", "phone", "mobile"]):
            steps.append({
                "index": 0,
                "description": "Capture Android phone screen",
                "tool_name": "android.screenshot",
                "parameters": {},
            })
            return steps

        # Standalone WhatsApp Automation Rule (Android ADB Bridge)
        if "whatsapp" in text_lower and any(k in text_lower for k in ["send", "message", "to", "hi", "hello"]):
            multi_matches = re.findall(
                r'(?:and\s+)?(?:send\s+)?(?:whatsapp\s+)?(?:message\s+)?(?:to\s+)?["\']([^"\']+)["\']\s+to\s+([a-zA-Z0-9_+\s,.:\-]+?)(?=\s+in\s+whatsapp|\s+on\s+whatsapp|\s+via\s+whatsapp|\s+and\s+send|\s+and\s+["\']|\s*$)',
                text,
                re.IGNORECASE
            )
            if not multi_matches:
                multi_matches_alt = re.findall(
                    r'\bto\s+([a-zA-Z0-9_+\s,.:\-]+?)\s+(?:send\s+)?(?:message\s+)?["\']([^"\']+)["\']',
                    text,
                    re.IGNORECASE
                )
                if multi_matches_alt:
                    multi_matches = [(m, p) for p, m in multi_matches_alt]

            msg_items = []
            if multi_matches:
                for m, p in multi_matches:
                    p_clean = re.sub(r'(?i)\s*\b(?:in|after|at|delay|every)\s+\d+.*$', '', p).strip() or p
                    parts = [part.strip() for part in re.split(r',|\n|\band\b|\b&\b', p_clean, flags=re.IGNORECASE) if part.strip()]
                    for sub_p in parts:
                        msg_items.append({"phone": sub_p, "message": m.strip()})
            else:
                saying_match = re.search(r'\bsaying\s+["\']?([^"\']+)["\']?$', text, re.IGNORECASE)
                quoted_match = re.search(r'["\']([^"\']+)["\']', text)
                if saying_match:
                    msg_content = saying_match.group(1).strip()
                    text_rec = re.sub(r'(?i)\s*\bsaying\s+["\']?([^"\']+)["\']?$', '', text)
                elif quoted_match:
                    msg_content = quoted_match.group(1).strip()
                    text_rec = text
                else:
                    msg_content = ""
                    text_rec = text

                recipient_match = re.search(r"\bto\s+([a-zA-Z0-9_+\s,]+?)(?:\s+saying|\s+message|\s+and\s+send|\s*\"|\s*$)", text_rec, re.IGNORECASE)
                rec_str = recipient_match.group(1).strip() if recipient_match else ""

                if not msg_content:
                    unquoted_match = re.search(r'(?:send\s+)?(?:whatsapp\s+)?(?:message[sd]?\s+)?(.+?)\s+to\s+([a-zA-Z0-9_+\s,.:\-]+)', text_rec, re.IGNORECASE)
                    if unquoted_match:
                        raw_msg = unquoted_match.group(1).strip()
                        for prefix in ["send whatsapp message", "send whatsapp messaged", "whatsapp message", "whatsapp messaged", "send message", "send messaged", "send whatsapp", "whatsapp", "messaged", "message"]:
                            if raw_msg.lower().startswith(prefix):
                                raw_msg = raw_msg[len(prefix):].strip()
                        if raw_msg.lower() in ["message", "messaged", "whatsapp message", "send message", "send whatsapp message", ""]:
                            msg_content = "Hello from NEXA"
                        else:
                            msg_content = raw_msg or "Hello from NEXA"
                        if not rec_str:
                            rec_str = unquoted_match.group(2).strip()
                    else:
                        msg_content = "Hello from NEXA"

                if not rec_str:
                    rec_str = "user 2"

                # Clean recipient string: strip "on whatsapp", "in whatsapp", "via whatsapp", "on phone", and schedule/time phrases
                rec_str = re.sub(r'(?i)\s*\b(?:on|in|via)\s+(?:whatsapp|phone|android)\b', '', rec_str).strip()
                rec_str = re.sub(r'(?i)\s*\b(?:in|after|at|delay|every)\s+\d+.*$', '', rec_str).strip() or rec_str

                # Clean message content: strip trailing "on whatsapp" if leaked into message
                msg_content = re.sub(r'(?i)\s*\b(?:on|in|via)\s+(?:whatsapp|phone|android)\b', '', msg_content).strip() or msg_content

                parts = [part.strip() for part in re.split(r',|\n|\band\b|\b&\b', rec_str, flags=re.IGNORECASE) if part.strip()]
                if len(parts) > 1:
                    msg_items = [{"phone": sub_p, "message": msg_content} for sub_p in parts]
                else:
                    recipient = parts[0] if parts else "user 2"

            unquoted_text = re.sub(r"'[^']*'|\"[^\"]*\"", "", text_lower)
            is_scheduled = any(k in unquoted_text for k in ["schedule", "tonight", "tomorrow"]) or bool(re.search(r'\b(?:at|in|after|delay|every)\s+(?:\d+|tonight|tomorrow)', unquoted_text))
            sched_time = ""
            if is_scheduled:
                time_match = re.search(r'\b(?:at|in|after|delay|every)\s+([0-9:.\sa-zA-Z]+?)(?=\s+on|\s+whatsapp|\s*$)', text, re.IGNORECASE)
                if time_match:
                    sched_time = time_match.group(0).strip()
                elif "tonight" in text_lower:
                    sched_time = "tonight at 12:00 AM"

            tool_to_use = "android.schedule_whatsapp" if is_scheduled else "android.send_whatsapp"

            if msg_items and len(msg_items) > 1:
                params = {"messages": msg_items}
                if is_scheduled and sched_time:
                    params["time"] = sched_time
                steps.append({
                    "index": 0,
                    "description": f"{'Schedule' if is_scheduled else 'Send'} WhatsApp messages to {len(msg_items)} recipient(s) on Android phone",
                    "tool_name": tool_to_use,
                    "parameters": params,
                })
            elif msg_items and len(msg_items) == 1:
                single_p = msg_items[0]["phone"]
                single_m = msg_items[0]["message"]
                params = {"phone": single_p, "message": single_m}
                if is_scheduled and sched_time:
                    params["time"] = sched_time
                steps.append({
                    "index": 0,
                    "description": f"{'Schedule' if is_scheduled else 'Send'} WhatsApp message '{single_m}' to '{single_p}' on Android phone",
                    "tool_name": tool_to_use,
                    "parameters": params,
                })
            else:
                params = {"phone": recipient, "message": msg_content}
                if is_scheduled and sched_time:
                    params["time"] = sched_time
                steps.append({
                    "index": 0,
                    "description": f"{'Schedule' if is_scheduled else 'Send'} WhatsApp message '{msg_content}' to '{recipient}' on Android phone",
                    "tool_name": tool_to_use,
                    "parameters": params,
                })
            return steps

        # Pattern 0: Android Device & In-App Activity Automation
        if any(k in text_lower for k in ["android", "phone", "mobile"]):
            if any(k in text_lower for k in ["google", "chrome", "search", "browser"]) and not any(k in text_lower for k in ["whatsapp", "youtube", "install", "device"]):
                clean_q = text
                for prefix in [
                    "search in google for", "search in google", "search in chrome for", "search in chrome",
                    "open chrome and", "open chrome", "open google and", "open google", "open browser and", "open browser",
                    "search google for", "search google", "google search for", "google search",
                    "search for", "search in", "search", "google", "chrome", "on phone", "on android", "in phone", "in android"
                ]:
                    clean_q = re.sub(rf"(?i)\b{re.escape(prefix)}\b", "", clean_q)
                clean_search = re.sub(r'\s+', ' ', clean_q).strip(" /:'\"") or "python tutorials"
                import urllib.parse
                encoded_search = urllib.parse.quote_plus(clean_search)
                search_intent_url = f"https://www.google.com/search?q={encoded_search}"

                steps.append({
                    "index": 0,
                    "description": f"Open Chrome on Android phone for Google Search: '{clean_search}'",
                    "tool_name": "android.launch_app",
                    "parameters": {"name": "chrome", "url": search_intent_url},
                })
                return steps

            if "type" in text_lower or "input" in text_lower or "write" in text_lower:
                input_txt = re.sub(r'(?i)\b(?:type|input|write|on android|on phone|in android|in phone)\b', '', text).strip(" '\":")
                clean_txt = input_txt or "Hello from NEXA"
                steps.append({
                    "index": 0,
                    "description": f"Type '{clean_txt}' into active field on Android phone",
                    "tool_name": "android.type",
                    "parameters": {"text": clean_txt, "press_enter": True},
                })
                return steps
            elif "device" in text_lower or "connect" in text_lower or "devices" in text_lower:
                steps.append({
                    "index": 0,
                    "description": "List connected Android phones/tablets",
                    "tool_name": "android.devices",
                    "parameters": {},
                })
                return steps
            elif "app" in text_lower and ("list" in text_lower or "show" in text_lower or "get" in text_lower):
                steps.append({
                    "index": 0,
                    "description": "List installed apps on Android phone",
                    "tool_name": "android.list_apps",
                    "parameters": {},
                })
                return steps
            elif "open" in text_lower or "launch" in text_lower:
                app_name = text
                for p in ["open", "launch", "on android", "on phone", "in android", "in phone", "app"]:
                    app_name = re.sub(rf"(?i)\b{re.escape(p)}\b", "", app_name)
                app_name = app_name.strip(" /:")
                if not app_name:
                    app_name = "whatsapp"
                steps.append({
                    "index": 0,
                    "description": f"Launch '{app_name}' on Android phone",
                    "tool_name": "android.launch_app",
                    "parameters": {"name": app_name},
                })
                return steps

        # Pattern 1: Screenshots
        elif "screenshot" in text_lower or "capture screen" in text_lower:
            steps.append({
                "index": 0,
                "description": "Capture screen image",
                "tool_name": "screen.capture",
                "parameters": {},
            })

        # Pattern 2: System info / RAM / CPU / Processes
        elif any(k in text_lower for k in ["system info", "cpu", "ram", "memory", "battery", "hardware"]):
            steps.append({
                "index": 0,
                "description": "Fetch system information metrics",
                "tool_name": "os.system_info",
                "parameters": {},
            })

        # Pattern 3: Process list / running applications
        elif "running" in text_lower or "processes" in text_lower or "app list" in text_lower:
            steps.append({
                "index": 0,
                "description": "List running applications and processes",
                "tool_name": "os.processes",
                "parameters": {"limit": 25},
            })

        # Pattern 4: Search files / search computer
        elif "search" in text_lower and ("file" in text_lower or "pdf" in text_lower or "computer" in text_lower or "doc" in text_lower):
            file_type = ""
            if "pdf" in text_lower:
                file_type = ".pdf"
            elif "java" in text_lower:
                file_type = ".java"
            elif "python" in text_lower or "py" in text_lower:
                file_type = ".py"

            steps.append({
                "index": 0,
                "description": f"Search files matching requested pattern",
                "tool_name": "filesystem.search",
                "parameters": {
                    "query": "*",
                    "file_type": file_type,
                    "max_results": 20,
                },
            })

        # Pattern 4.5: Movie & Software Download Automation (Windows & Android)
        elif "download" in text_lower or "movie" in text_lower or "karuppu" in text_lower or "moviesda" in text_lower:
            dl_query = text
            for p in ["for window and android", "for windows and android", "for window", "for windows", "for android", "for phone", "open google and", "open google", "download the requirement that want by user", "download the requirement", "download"]:
                dl_query = re.sub(rf"(?i)\b{re.escape(p)}\b", "", dl_query)
            clean_dl = dl_query.strip(" /:") or "karuppu"

            if "android" in text_lower or "phone" in text_lower:
                steps.append({
                    "index": 0,
                    "description": f"Launch Chrome on Android phone for download: {clean_dl}",
                    "tool_name": "android.launch_app",
                    "parameters": {"name": "chrome"},
                })
                steps.append({
                    "index": 1,
                    "description": f"Search download query '{clean_dl}' in Chrome on phone",
                    "tool_name": "android.type",
                    "parameters": {"text": f"https://www.google.com/search?q={clean_dl.replace(' ', '+')}"},
                })
            else:
                steps.append({
                    "index": 0,
                    "description": f"Download movie/file directly via Moviesda browser automation: {clean_dl}",
                    "tool_name": "browser.download",
                    "parameters": {
                        "query": clean_dl,
                        "file_type": "software" if any(k in text_lower for k in ["software", ".exe", ".apk", "setup", "installer", "app", "vs code", "chrome", "python"]) else "movie",

                        "quality": "720p" if "720p" in text_lower else ("480p" if "480p" in text_lower else "720p"),
                    },
                })


        # Pattern 5: Open browser / search YouTube / search web (Windows & Android)
        elif any(k in text_lower for k in ["browser", "youtube", "google", "chrome", "search", "play", "video", "song"]):
            clean_q = text
            for prefix in [
                "search in google for", "search in google", "search in chrome for", "search in chrome",
                "open chrome and", "open chrome", "open browser and", "open browser",
                "search youtube for", "search youtube", "search google for", "search google",
                "google search for", "google search", "google link for", "google link", "google",
                "search for", "search in", "search", "play recent video", "play high views video",
                "play top video", "play video", "play song", "play", "in chrome", "in google", "on chrome", "on google"
            ]:
                clean_q = re.sub(rf"(?i)\b{re.escape(prefix)}\b", "", clean_q)
            query = re.sub(r'\s+', ' ', clean_q).strip(" /:") or text.strip()

            is_youtube = any(k in text_lower for k in ["youtube", "play", "video", "song", "dsa"])
            is_play = "play" in text_lower or "watch" in text_lower or "song" in text_lower or ("video" in text_lower and not "search" in text_lower)

            sp_param = ""
            sort_desc = "relevant"
            if any(k in text_lower for k in ["recent", "latest", "newest", "new"]):
                sp_param = "&sp=CAI%253D"
                sort_desc = "most recent"
            elif any(k in text_lower for k in ["high views", "most viewed", "popular", "most views"]):
                sp_param = "&sp=CAM%253D"
                sort_desc = "highest views"

            if is_youtube:
                import urllib.parse, urllib.request
                encoded = urllib.parse.quote_plus(query)
                target_url = f"https://www.youtube.com/results?search_query={encoded}{sp_param}"

                # For Play mode on Windows, fetch direct watch?v= URL for instant auto-play
                if is_play:
                    try:
                        req = urllib.request.Request(
                            target_url,
                            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                        )
                        with urllib.request.urlopen(req, timeout=3) as resp:
                            html = resp.read().decode("utf-8", errors="ignore")
                            vids = re.findall(r'/watch\?v=([a-zA-Z0-9_-]{11})', html)
                            if vids:
                                target_url = f"https://www.youtube.com/watch?v={vids[0]}"
                    except Exception:
                        pass

                steps.append({
                    "index": 0,
                    "description": f"{'Play' if is_play else 'Search'} '{query}' ({sort_desc}) on YouTube in Windows browser",
                    "tool_name": "browser.open",
                    "parameters": {"url": target_url},
                })
            else:
                steps.append({
                    "index": 0,
                    "description": f"Open browser and search: {query}",
                    "tool_name": "browser.search",
                    "parameters": {
                        "query": query,
                        "site": "",
                    },
                })

        # Pattern 0.4: GitHub Pushing / Repository Automation
        elif "github" in text_lower or ("git" in text_lower and "push" in text_lower):
            if "phone" in text_lower or "android" in text_lower:
                steps.append({
                    "index": 0,
                    "description": "Launch GitHub app on Android phone",
                    "tool_name": "android.launch_app",
                    "parameters": {"name": "github"},
                })
            else:
                steps.append({
                    "index": 0,
                    "description": "Open GitHub in browser to view / push repository",
                    "tool_name": "browser.open",
                    "parameters": {"url": "https://github.com"},
                })

        # Pattern 0.5: LinkedIn Social & Networking Automation
        elif "linkedin" in text_lower:
            if "phone" in text_lower or "android" in text_lower:
                steps.append({
                    "index": 0,
                    "description": "Launch LinkedIn app on Android phone",
                    "tool_name": "android.launch_app",
                    "parameters": {"name": "linkedin"},
                })
            else:
                steps.append({
                    "index": 0,
                    "description": "Open LinkedIn in browser to view / post update",
                    "tool_name": "browser.open",
                    "parameters": {"url": "https://www.linkedin.com"},
                })

        # Pattern 0.6: Messaging & Multi-Step Desktop App / Android Interaction (e.g. WhatsApp, Telegram, Notepad)
        elif any(k in text_lower for k in ["whatsapp", "whatapp", "whatsap", "watsapp", "wsp", "telegram", "notepad", "mail"]) and any(k in text_lower for k in ["send", "message", "type", "write", "hi", "hello", "help"]):
            target_app = "whatsapp" if any(k in text_lower for k in ["whatsapp", "whatapp", "whatsap", "watsapp", "wsp"]) else ("telegram" if "telegram" in text_lower else ("notepad" if "notepad" in text_lower else "mail"))
            is_android = True if target_app == "whatsapp" else (any(k in text_lower for k in ["android", "phone", "mobile"]) or "android" in text_lower)

            # Check for multiple recipients/messages
            multi_matches = re.findall(
                r'(?:and\s+)?(?:send\s+)?(?:whatsapp\s+)?(?:message\s+)?(?:to\s+)?["\']([^"\']+)["\']\s+to\s+([a-zA-Z0-9_+\s]+?)(?=\s*,|\s+and|\s+send|\s*$)',
                text,
                re.IGNORECASE
            )

            if not multi_matches:
                multi_matches_alt = re.findall(
                    r'\bto\s+([a-zA-Z0-9_+\s]+?)\s+(?:send\s+)?(?:message\s+)?["\']([^"\']+)["\']',
                    text,
                    re.IGNORECASE
                )
                if multi_matches_alt:
                    multi_matches = [(m, p) for p, m in multi_matches_alt]

            if is_android and target_app == "whatsapp":
                msg_items = []
                if multi_matches:
                    for m, p in multi_matches:
                        parts = [part.strip() for part in re.split(r',|\n|\band\b|\b&\b', p, flags=re.IGNORECASE) if part.strip()]
                        for sub_p in parts:
                            msg_items.append({"phone": sub_p, "message": m.strip()})
                else:
                    quoted_match = re.search(r'["\']([^"\']+)["\']', text)
                    msg_content = quoted_match.group(1).strip() if quoted_match else ""
                    recipient_match = re.search(r"\bto\s+([a-zA-Z0-9_+\s,]+?)(?:\s+saying|\s+message|\s+and\s+send|\s*\"|\s*$)", text, re.IGNORECASE)
                    rec_str = recipient_match.group(1).strip() if recipient_match else ""

                    if not msg_content:
                        unquoted_match = re.search(r'(?:send\s+)?(?:whatsapp\s+)?(?:message\s+)?(.+?)\s+to\s+([a-zA-Z0-9_+\s,]+)', text, re.IGNORECASE)
                        if unquoted_match:
                            raw_msg = unquoted_match.group(1).strip()
                            for prefix in ["send whatsapp message", "whatsapp message", "send message", "send whatsapp", "whatsapp"]:
                                if raw_msg.lower().startswith(prefix):
                                    raw_msg = raw_msg[len(prefix):].strip()
                            msg_content = raw_msg or "Hello from NEXA"
                            if not rec_str:
                                rec_str = unquoted_match.group(2).strip()
                        else:
                            msg_content = "Hello from NEXA"

                    # Strip schedule/time phrases from recipient string
                    rec_str = re.sub(r'(?i)\b(?:in|after|at|delay|every)\s+\d+.*$', '', rec_str).strip() or rec_str

                    parts = [part.strip() for part in re.split(r',|\n|\band\b|\b&\b', rec_str, flags=re.IGNORECASE) if part.strip()]
                    if len(parts) > 1:
                        msg_items = [{"phone": sub_p, "message": msg_content} for sub_p in parts]
                    else:
                        recipient = parts[0] if parts else ""

                is_scheduled = any(k in text_lower for k in ["schedule", "at ", "in ", "after", "delay", "every", "tonight", "tomorrow"])
                sched_time = ""
                if is_scheduled:
                    time_match = re.search(r'\b(?:at|in|after|delay|every)\s+([0-9:.\sa-zA-Z]+?)(?=\s+on|\s+whatsapp|\s*$)', text, re.IGNORECASE)
                    if time_match:
                        sched_time = time_match.group(0).strip()
                    elif "tonight" in text_lower:
                        sched_time = "tonight at 12:00 AM"

                tool_to_use = "android.schedule_whatsapp" if is_scheduled else "android.send_whatsapp"

                if msg_items:
                    params = {"messages": msg_items}
                    if is_scheduled and sched_time:
                        params["time"] = sched_time
                    steps.append({
                        "index": 0,
                        "description": f"{'Schedule' if is_scheduled else 'Send'} WhatsApp messages to {len(msg_items)} recipient(s) on Android phone",
                        "tool_name": tool_to_use,
                        "parameters": params,
                    })
                else:
                    params = {"phone": recipient, "message": msg_content}
                    if is_scheduled and sched_time:
                        params["time"] = sched_time
                    steps.append({
                        "index": 0,
                        "description": f"{'Schedule' if is_scheduled else 'Send'} WhatsApp message '{msg_content}' to '{recipient}' on Android phone",
                        "tool_name": tool_to_use,
                        "parameters": params,
                    })
            else:
                if multi_matches and len(multi_matches) > 1:
                    # Multi-recipient desktop execution flow
                    steps.append({
                        "index": 0,
                        "description": f"Launch {target_app.capitalize()} application",
                        "tool_name": "app.launch",
                        "parameters": {"name": target_app},
                    })
                    step_idx = 1
                    for m_text, rec in multi_matches:
                        rec = rec.strip()
                        m_text = m_text.strip()
                        steps.append({
                            "index": step_idx,
                            "description": f"Focus search for recipient '{rec}'",
                            "tool_name": "keyboard.hotkey",
                            "parameters": {"keys": "ctrl+f"},
                        })
                        step_idx += 1
                        steps.append({
                            "index": step_idx,
                            "description": f"Type recipient name '{rec}'",
                            "tool_name": "keyboard.type",
                            "parameters": {"text": rec},
                        })
                        step_idx += 1
                        steps.append({
                            "index": step_idx,
                            "description": f"Select contact '{rec}'",
                            "tool_name": "keyboard.press",
                            "parameters": {"key": "enter"},
                        })
                        step_idx += 1
                        steps.append({
                            "index": step_idx,
                            "description": f"Type message '{m_text}'",
                            "tool_name": "keyboard.type",
                            "parameters": {"text": m_text},
                        })
                        step_idx += 1
                        steps.append({
                            "index": step_idx,
                            "description": "Send message (Press Enter)",
                            "tool_name": "keyboard.press",
                            "parameters": {"key": "enter"},
                        })
                        step_idx += 1
                else:
                    # Single recipient desktop flow
                    recipient_match = re.search(r"\bto\s+([a-zA-Z0-9_\s]+?)(?:\s+message|\s+and|\s+send|\s*\"|\s*$)", text, re.IGNORECASE)
                    recipient = recipient_match.group(1).strip() if recipient_match else ""
                    quoted_match = re.search(r'["\']([^"\']+)["\']', text)
                    if quoted_match:
                        msg_content = quoted_match.group(1).strip()
                    else:
                        msg_match = re.search(r'(?:message|send|type|write)\s+(.+?)(?:\s+to|\s*$)', text, re.IGNORECASE)
                        msg_content = msg_match.group(1).strip() if msg_match else ""

                    if recipient and f"to {recipient}" in msg_content.lower():
                        msg_content = re.sub(rf"(?i)\bto\s+{re.escape(recipient)}\b", "", msg_content).strip()
                    if not msg_content:
                        msg_content = "hello"

                    steps.append({
                        "index": 0,
                        "description": f"Launch {target_app.capitalize()} application",
                        "tool_name": "app.launch",
                        "parameters": {"name": target_app},
                    })
                    step_idx = 1
                    if recipient and target_app in ("whatsapp", "telegram", "mail"):
                        steps.append({
                            "index": step_idx,
                            "description": f"Focus search for recipient '{recipient}'",
                            "tool_name": "keyboard.hotkey",
                            "parameters": {"keys": "ctrl+f"},
                        })
                        step_idx += 1
                        steps.append({
                            "index": step_idx,
                            "description": f"Type recipient name '{recipient}'",
                            "tool_name": "keyboard.type",
                            "parameters": {"text": recipient},
                        })
                        step_idx += 1
                        steps.append({
                            "index": step_idx,
                            "description": "Select contact",
                            "tool_name": "keyboard.press",
                            "parameters": {"key": "enter"},
                        })
                        step_idx += 1
                    steps.append({
                        "index": step_idx,
                        "description": f"Type message '{msg_content}'",
                        "tool_name": "keyboard.type",
                        "parameters": {"text": msg_content},
                    })
                    step_idx += 1
                    if target_app in ("whatsapp", "telegram", "mail"):
                        steps.append({
                            "index": step_idx,
                            "description": "Send message (Press Enter)",
                            "tool_name": "keyboard.press",
                            "parameters": {"key": "enter"},
                        })

        # Pattern 6: Launch application
        elif "open" in text_lower or "launch" in text_lower:
            app_name = text.replace("open", "").replace("launch", "").strip()
            if not app_name:
                app_name = "notepad"

            steps.append({
                "index": 0,
                "description": f"Launch application: {app_name}",
                "tool_name": "app.launch",
                "parameters": {"name": app_name},
            })

        # Default fallback multi-step plan
        if not steps:
            steps = [
                {
                    "index": 0,
                    "description": f"Check system status for goal: {text[:50]}",
                    "tool_name": "os.system_info",
                    "parameters": {},
                },
                {
                    "index": 1,
                    "description": "Capture screen snapshot",
                    "tool_name": "screen.capture",
                    "parameters": {},
                },
            ]

        return steps

    def _summarize_user_content(self, text: str) -> str:
        if "Goal:" in text:
            match = re.search(r"Goal:\s*(.*?)(?:\n|$)", text)
            goal_name = match.group(1).strip() if match else text[:60]
            if "Results: None" in text or "Steps completed: 0" in text:
                return f"NEXA completed processing for goal: '{goal_name}'."
            return f"NEXA successfully executed goal: '{goal_name}'."
        return f"NEXA processed: '{text}'."


class RuleProvider(LocalRuleProvider):
    """
    Alias / Extension of LocalRuleProvider for intent parsing and test support.
    """
    def generate_fallback_plan(self, text: str) -> Plan:
        raw_steps = self._generate_rule_plan(text)
        step_objs = [
            PlanStep(
                tool_name=s.get("tool_name", ""),
                parameters=s.get("parameters", {}),
                description=s.get("description", "")
            )
            for s in raw_steps
        ]
        return Plan(step_objs)

