"""
Paper2Slides package initialization.
"""

from __future__ import annotations

import os


def _clear_bad_loopback_proxies() -> None:
    """
    Clear obviously broken local proxy settings.

    Some Windows shells inherit placeholder proxy values such as
    ``http://127.0.0.1:9`` which cause every outbound API request to fail.
    We only clear these known-bad loopback placeholders to avoid breaking
    legitimate proxy configurations.
    """
    bad_values = {
        "http://127.0.0.1:9",
        "https://127.0.0.1:9",
        "http://localhost:9",
        "https://localhost:9",
    }

    for key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
        value = os.environ.get(key, "").strip().lower()
        if value in bad_values:
            os.environ.pop(key, None)


_clear_bad_loopback_proxies()
