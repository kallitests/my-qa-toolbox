"""
SmokeSentinel — Playwright MCP Client
Wraps the Playwright MCP server HTTP API into clean Python calls.
"""

import os
import httpx
from typing import Any


MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:3001")
DEFAULT_TIMEOUT_MS = int(os.getenv("SMOKE_TEST_TIMEOUT_MS", "30000"))


class PlaywrightMCPClient:
    """
    HTTP client for the Playwright MCP server.
    The agent sends tool calls; the server pilots a real Chromium browser.
    """

    def __init__(self, base_url: str = MCP_SERVER_URL):
        self.base_url = base_url
        self._client = httpx.Client(timeout=DEFAULT_TIMEOUT_MS / 1000 + 5)

    def call(self, tool: str, params: dict, timeout_ms: int = DEFAULT_TIMEOUT_MS) -> dict:
        """
        Send a single tool call to the Playwright MCP server.

        Args:
            tool:       Tool name (e.g. "playwright_navigate")
            params:     Tool parameters dict
            timeout_ms: Per-call timeout in ms

        Returns:
            dict with keys: success, result, error, duration_ms
        """
        import time
        start = time.monotonic()

        try:
            response = self._client.post(
                f"{self.base_url}/tools/call",
                json={"tool": tool, "params": params},
                timeout=(timeout_ms / 1000) + 2,
            )
            duration_ms = int((time.monotonic() - start) * 1000)

            if response.status_code == 200:
                return {
                    "success": True,
                    "result": response.json(),
                    "error": None,
                    "duration_ms": duration_ms,
                }
            else:
                return {
                    "success": False,
                    "result": None,
                    "error": f"HTTP {response.status_code}: {response.text[:200]}",
                    "duration_ms": duration_ms,
                }
        except httpx.TimeoutException:
            duration_ms = int((time.monotonic() - start) * 1000)
            return {
                "success": False,
                "result": None,
                "error": f"MCP call timed out after {timeout_ms}ms",
                "duration_ms": duration_ms,
            }
        except Exception as e:
            duration_ms = int((time.monotonic() - start) * 1000)
            return {
                "success": False,
                "result": None,
                "error": str(e),
                "duration_ms": duration_ms,
            }

    def navigate(self, url: str) -> dict:
        return self.call("playwright_navigate", {"url": url})

    def click(self, selector: str) -> dict:
        return self.call("playwright_click", {"selector": selector})

    def fill(self, selector: str, value: str) -> dict:
        return self.call("playwright_fill", {"selector": selector, "value": value})

    def expect_visible(self, selector: str, timeout_ms: int = 5000) -> dict:
        return self.call("playwright_expect_visible", {"selector": selector, "timeout": timeout_ms})

    def get_accessibility_tree(self) -> dict:
        """Get current page accessibility tree — used by healer to find alternative selectors."""
        return self.call("playwright_get_accessibility_tree", {})

    def screenshot(self, path: str) -> dict:
        return self.call("playwright_screenshot", {"path": path})

    def health(self) -> bool:
        try:
            r = self._client.get(f"{self.base_url}/health", timeout=3)
            return r.status_code == 200
        except Exception:
            return False

    def __del__(self):
        try:
            self._client.close()
        except Exception:
            pass
