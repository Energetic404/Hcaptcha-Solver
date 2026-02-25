#!/usr/bin/env python3
"""
Example: solve hCaptcha remotely using Playwright (Chromium) and hcaptchasolver.com.

Usage:
  python main.py [options] [<server_url>] [<api_key>]

Environment:
  HCAPTCHA_SERVER_URL  - Base URL (default: https://hcaptchasolver.com)
  HCAPTCHA_CLIENT_KEY  - Your client API key (required unless passed as arg)
  HCAPTCHA_PAGE_URL    - Page to open (default: https://accounts.hcaptcha.com/demo)
  HCAPTCHA_WAIT_TIMEOUT - Max seconds to wait for captcha (empty = wait forever)
  HCAPTCHA_DELAY_AFTER_LOAD - Seconds after captcha loads before first screenshot (default: 5)
  HCAPTCHA_KEEP_OPEN   - "0" or "false" to close browser immediately after solve
  HCAPTCHA_OPENS_AUTOMATICALLY - "1" or "true" if the page opens the captcha itself (e.g. Discord)
  HCAPTCHA_HEADLESS    - "1" or "true" to run browser headless
"""
from __future__ import annotations

import os
import sys

# Load .env from current directory so HCAPTCHA_CLIENT_KEY etc. are available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from playwright.sync_api import sync_playwright

from api_client import RemoteSessionApiClient
from solver_playwright import run_solve, _log


def _env_bool(name: str, default: bool = False) -> bool:
    v = os.environ.get(name, "").strip().lower()
    return v in ("1", "true", "yes") if v else default


def _env_float(name: str, default: float | None = None) -> float | None:
    v = os.environ.get(name, "").strip()
    if not v:
        return default
    try:
        return float(v)
    except ValueError:
        return default


def main() -> int:
    server_url = os.environ.get("HCAPTCHA_SERVER_URL", "https://hcaptchasolver.com")
    api_key = os.environ.get("HCAPTCHA_CLIENT_KEY", "").strip()
    if len(sys.argv) >= 2:
        if sys.argv[1].startswith("http"):
            server_url = sys.argv[1]
            api_key = (sys.argv[2] if len(sys.argv) >= 3 else os.environ.get("HCAPTCHA_CLIENT_KEY", "")).strip()
        else:
            api_key = sys.argv[1].strip()
    if not api_key:
        print("Error: Set HCAPTCHA_CLIENT_KEY or pass: python main.py [<serverUrl>] <apiKey>")
        return 1

    page_url = os.environ.get("HCAPTCHA_PAGE_URL", "https://accounts.hcaptcha.com/demo")
    wait_timeout = _env_float("HCAPTCHA_WAIT_TIMEOUT")
    delay_after_load = _env_float("HCAPTCHA_DELAY_AFTER_LOAD", 5.0) or 5.0
    keep_open = _env_bool("HCAPTCHA_KEEP_OPEN", True)
    captcha_opens_automatically = _env_bool("HCAPTCHA_OPENS_AUTOMATICALLY") or ("discord.com" in page_url.lower())
    headless = _env_bool("HCAPTCHA_HEADLESS", False)

    api = RemoteSessionApiClient(server_url, api_key)
    _log("Launching browser (Playwright Chromium)...")
    with sync_playwright() as play:
        try:
            browser = play.chromium.launch(headless=headless)
        except Exception as e:
            err = str(e).lower()
            if "executable doesn't exist" in err or "executable does not exist" in err or ("playwright" in err and "install" in err):
                print("\nPlaywright browsers are not installed. Run:", file=sys.stderr)
                print("  playwright install", file=sys.stderr)
                print("or (Chromium only):  playwright install chromium", file=sys.stderr)
                print("", file=sys.stderr)
            raise
        try:
            context = browser.new_context(viewport={"width": 1280, "height": 720})
            page = context.new_page()
            _log("Loading page: %s" % page_url)
            page.goto(page_url, wait_until="domcontentloaded")
            task_id = run_solve(
                page,
                api,
                page_url,
                wait_captcha_timeout=wait_timeout,
                delay_after_captcha_load=delay_after_load,
                captcha_opens_automatically=captcha_opens_automatically,
            )
            if task_id is None:
                _log("Solve failed")
                return 1
            if keep_open:
                _log("Press Enter to close the browser...")
                input("Press Enter to close the browser...")
            return 0
        except TimeoutError as e:
            _log("Timeout: %s" % e)
            return 1
        except Exception as e:
            _log("Error: %s" % e)
            import traceback
            traceback.print_exc()
            return 1
        finally:
            browser.close()


if __name__ == "__main__":
    sys.exit(main())
