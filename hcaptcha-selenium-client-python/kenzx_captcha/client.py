"""
Remote hCaptcha client for captcha-platform / hcaptchasolver.com.

Use RemoteCaptchaClient with your server URL and API key. Call run() to open a browser,
navigate to your page, wait for the captcha, and let a worker solve it remotely.
Use solve() with your own WebDriver for more control (e.g. custom navigation).
"""
from __future__ import annotations

import traceback
from typing import Optional, Any, Callable

from selenium import webdriver

from kenzx_captcha.api_client import _ApiClient
from kenzx_captcha._solver import run_solve, _log

try:
    import undetected_chromedriver as uc
    _HAS_UC = True
except ImportError:
    _HAS_UC = False


# Chrome flags that often prevent crashes on heavy sites (e.g. Discord)
_STABLE_MODE_ARGS = [
    "--disable-gpu",
    "--disable-software-rasterizer",
    "--disable-dev-shm-usage",
    "--no-sandbox",
    "--disable-gpu-sandbox",
    "--disable-gpu-shader-disk-cache",
    "--disable-features=TranslateUI",  # reduce process load
    "--disable-accelerated-2d-canvas",
    "--disable-backgrounding-occluded-windows",
    "--renderer-process-limit=1",
]


def _chrome_options(headless: bool = False, stable_mode: bool = False) -> Any:
    """Build Chrome options (Selenium). Used when undetected_chromedriver is not used."""
    opts = webdriver.ChromeOptions()
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_argument("--disable-dev-shm-usage")
    if stable_mode:
        for arg in _STABLE_MODE_ARGS:
            opts.add_argument(arg)
    if headless:
        opts.add_argument("--headless=new")
    return opts


def create_driver(
    use_undetected: bool = True,
    headless: bool = False,
    stable_mode: bool = False,
) -> Any:
    """
    Create a Chrome WebDriver. With use_undetected=True (default), uses
    undetected-chromedriver so sites don't block. Use stable_mode=True for
    heavy sites like Discord to reduce Chrome crashes (disables GPU/sandbox).
    """
    if use_undetected and _HAS_UC:
        opts = uc.ChromeOptions()
        opts.add_argument("--disable-dev-shm-usage")
        if stable_mode:
            for arg in _STABLE_MODE_ARGS:
                opts.add_argument(arg)
        if headless:
            opts.add_argument("--headless=new")
        return uc.Chrome(options=opts)
    opts = _chrome_options(headless=headless, stable_mode=stable_mode)
    return webdriver.Chrome(options=opts)


def _create_chrome_driver(
    use_undetected: bool,
    headless: bool,
    stable_mode: bool = False,
) -> Any:
    return create_driver(
        use_undetected=use_undetected,
        headless=headless,
        stable_mode=stable_mode,
    )


class RemoteCaptchaClient:
    """
    Client for remote hCaptcha solving (captcha-platform / hcaptchasolver.com).
    Use run() to open the browser and solve in one call, or solve() with your own driver.
    """

    def __init__(self, server_url: str, api_key: str):
        self.server_url = server_url.rstrip("/")
        self.api_key = api_key.strip()
        self._api = _ApiClient(self.server_url, self.api_key)

    def solve(
        self,
        driver: Any,
        page_url: str = "https://accounts.hcaptcha.com/demo",
        wait_captcha_timeout: Optional[float] = None,
        delay_after_captcha_load: float = 5.0,
        captcha_opens_automatically: bool = False,
        after_solve: Optional[Callable[[Any], None]] = None,
    ) -> Optional[str]:
        """
        Solve the captcha on the current page. Driver must already be on a page with hCaptcha.
        wait_captcha_timeout: max seconds to wait for captcha to appear (None = wait indefinitely).
        delay_after_captcha_load: seconds to wait after captcha is visible before sending first
            screenshot (default 5) to avoid null/blank screenshots while the widget is still rendering.
        captcha_opens_automatically: if True, do not click the checkbox; the page opens the captcha
            (e.g. Discord). Library only waits for it to be visible and expanded.
        after_solve: optional callback(driver) run after a successful solve (e.g. click submit button).
        Returns task_id if successful, None if create task failed.
        """
        task_id = run_solve(
            driver,
            self._api,
            page_url,
            wait_captcha_timeout=wait_captcha_timeout,
            delay_after_captcha_load=delay_after_captcha_load,
            captcha_opens_automatically=captcha_opens_automatically,
        )
        if task_id is not None and after_solve is not None:
            try:
                after_solve(driver)
            except Exception as e:
                _log("after_solve callback error: %s" % e)
        return task_id

    def run(
        self,
        page_url: str = "https://accounts.hcaptcha.com/demo",
        keep_browser_open: bool = True,
        headless: bool = False,
        use_undetected: bool = True,
        stable_mode: bool | None = None,
        wait_captcha_timeout: Optional[float] = None,
        delay_after_captcha_load: float = 5.0,
        captcha_opens_automatically: bool = False,
        after_solve: Optional[Callable[[Any], None]] = None,
    ) -> bool:
        """
        Open Chrome, load page_url, solve the captcha (worker solves remotely), then quit or wait.
        use_undetected=True uses undetected-chromedriver. stable_mode=True adds Chrome flags to
        reduce crashes on heavy sites (e.g. Discord); defaults to True when page_url contains 'discord.com'.
        wait_captcha_timeout: max seconds to wait for captcha to appear (None = wait indefinitely).
        delay_after_captcha_load: seconds to wait after captcha is visible before sending first
            screenshot (default 5) to avoid null/blank screenshots.
        captcha_opens_automatically: if True, do not click the checkbox; the page opens the captcha
            (e.g. Discord). Library only waits for it to be visible and expanded.
        after_solve: optional callback(driver) run after a successful solve (e.g. click submit button).
        Returns True if solved successfully, False on error.
        """
        if stable_mode is None:
            stable_mode = "discord.com" in page_url.lower()
        _log("Opening browser...")
        driver = _create_chrome_driver(
            use_undetected=use_undetected,
            headless=headless,
            stable_mode=stable_mode,
        )
        try:
            driver.set_window_size(1280, 720)
            _log("Loading page: %s" % page_url)
            driver.get(page_url)
            task_id = run_solve(
                driver,
                self._api,
                page_url,
                wait_captcha_timeout=wait_captcha_timeout,
                delay_after_captcha_load=delay_after_captcha_load,
                captcha_opens_automatically=captcha_opens_automatically,
            )
            if task_id is None:
                _log("Solve failed (create task or captcha not ready)")
                return False
            if after_solve is not None:
                try:
                    after_solve(driver)
                except Exception as e:
                    _log("after_solve callback error: %s" % e)
            if keep_browser_open:
                _log("Press Enter to close the browser...")
                input("Press Enter to close the browser...")
            return True
        except TimeoutError as e:
            _log("Timeout: %s" % e)
            return False
        except Exception as e:
            _log("Error: %s" % e)
            traceback.print_exc()
            return False
        finally:
            driver.quit()
