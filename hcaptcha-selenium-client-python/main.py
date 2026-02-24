#!/usr/bin/env python3
"""
Example: use kenzx_captcha to solve hCaptcha remotely (short code).

Usage:
  python main.py [options] [<server_url>] [<api_key>]

Environment:
  HCAPTCHA_SERVER_URL  - Base URL (default: https://hcaptchasolver.com)
  HCAPTCHA_CLIENT_KEY  - Your client API key (required unless passed as arg)
  HCAPTCHA_PAGE_URL    - Page to open (default: https://accounts.hcaptcha.com/demo)
  HCAPTCHA_WAIT_TIMEOUT - Max seconds to wait for captcha (empty = wait forever)
  HCAPTCHA_DELAY_AFTER_LOAD - Seconds to wait after captcha loads before first screenshot (default: 5)
  HCAPTCHA_STABLE_MODE - "1" or "true" for stable mode (recommended for Discord/heavy sites)
  HCAPTCHA_HEADLESS   - "1" or "true" to run browser headless
  HCAPTCHA_KEEP_OPEN  - "0" or "false" to close browser immediately after solve
  HCAPTCHA_OPENS_AUTOMATICALLY - "1" or "true" if the page opens the captcha itself (e.g. Discord).
      When set, the library does NOT click the checkbox; it only waits for the captcha to be visible and loaded.
  HCAPTCHA_CLICK_SUBMIT_AFTER_SOLVE - "1" or "true" to click the submit button after solve (e.g. hCaptcha demo #hcaptcha-demo-submit).
"""
import os
import sys

from selenium.webdriver.common.by import By

from kenzx_captcha import RemoteCaptchaClient


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


def _click_demo_submit_after_solve(driver):
    """Optional after_solve action: click the hCaptcha demo page submit button."""
    try:
        el = driver.find_element(By.XPATH, "//*[@id='hcaptcha-demo-submit']")
        if el:
            el.click()
            print("[kenzx_captcha] Clicked submit button.", flush=True)
    except Exception:
        try:
            el = driver.find_element(By.XPATH, "/html/body/div[5]/form/fieldset/ul/li[3]/input")
            if el:
                el.click()
                print("[kenzx_captcha] Clicked submit button.", flush=True)
        except Exception:
            pass


def main() -> int:
    # --- Server URL: first arg if it looks like a URL, else env, else default ---
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

    # --- Optional: page to open (e.g. Discord register, or demo) ---
    page_url = os.environ.get("HCAPTCHA_PAGE_URL", "https://accounts.hcaptcha.com/demo")

    # --- Optional: max seconds to wait for captcha to appear (None = wait forever) ---
    wait_timeout = _env_float("HCAPTCHA_WAIT_TIMEOUT")

    # --- Optional: delay after captcha loads before sending first screenshot (default 5s to avoid null screenshot) ---
    delay_after_load = _env_float("HCAPTCHA_DELAY_AFTER_LOAD", 5.0) or 5.0

    # --- Optional: stable mode for heavy sites like Discord (reduces Chrome crashes) ---
    stable_mode = _env_bool("HCAPTCHA_STABLE_MODE") or ("discord.com" in page_url.lower())

    # --- Optional: run browser headless ---
    headless = _env_bool("HCAPTCHA_HEADLESS", False)

    # --- Optional: keep browser open after solve (default True so you can see result) ---
    keep_open = _env_bool("HCAPTCHA_KEEP_OPEN", True)

    # --- Optional: page opens captcha automatically (e.g. Discord). If True, we don't click checkbox, only wait for load ---
    captcha_opens_automatically = _env_bool("HCAPTCHA_OPENS_AUTOMATICALLY") or ("discord.com" in page_url.lower())

    # --- Optional: after solve, run an action with the driver (e.g. click submit on demo page) ---
    click_submit_after = _env_bool("HCAPTCHA_CLICK_SUBMIT_AFTER_SOLVE", False)
    after_solve = _click_demo_submit_after_solve if click_submit_after else None

    client = RemoteCaptchaClient(server_url, api_key)
    ok = client.run(
        page_url=page_url,
        keep_browser_open=keep_open,
        headless=headless,
        use_undetected=True,
        stable_mode=stable_mode,
        wait_captcha_timeout=wait_timeout,
        delay_after_captcha_load=delay_after_load,
        captcha_opens_automatically=captcha_opens_automatically,
        after_solve=after_solve,
    )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
