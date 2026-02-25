"""Playwright-based remote solve flow for hcaptchasolver.com."""
from __future__ import annotations

import base64
import time
from dataclasses import dataclass
from typing import Optional

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from api_client import RemoteSessionApiClient, CropRectDto

MIN_SIZE = 260
POLL_S = 0.12
SCREENSHOT_INTERVAL_S = 0.2
LOG_PREFIX = "[hcaptcha-playwright]"


def _log(msg: str) -> None:
    print(f"{LOG_PREFIX} {msg}", flush=True)


@dataclass
class _CropRect:
    left: int
    top: int
    width: int
    height: int


def _get_viewport_and_crop(page: Page) -> tuple[Optional[_CropRect], int, int]:
    result = page.evaluate("""() => {
        const iframes = document.querySelectorAll('iframe[src*="hcaptcha.com"]');
        let best = null, bestArea = 0;
        for (let i = 0; i < iframes.length; i++) {
            const r = iframes[i].getBoundingClientRect();
            if (r.width < 50 || r.height < 50) continue;
            const area = r.width * r.height;
            if (area > bestArea) { bestArea = area; best = r; }
        }
        const w = window.innerWidth || 1280, h = window.innerHeight || 720;
        if (best) return { left: Math.round(best.left), top: Math.round(best.top), width: Math.round(best.width), height: Math.round(best.height), viewportW: w, viewportH: h };
        return { viewportW: w, viewportH: h };
    }""")
    if not result:
        return None, 1280, 720
    vw = int(result.get("viewportW") or 1280)
    vh = int(result.get("viewportH") or 720)
    rect = None
    if "left" in result:
        rect = _CropRect(
            left=int(result.get("left", 0)),
            top=int(result.get("top", 0)),
            width=int(result.get("width", 0)),
            height=int(result.get("height", 0)),
        )
    return rect, vw, vh


def _wait_for_iframe(page: Page, timeout: Optional[float] = None) -> None:
    _log("Waiting for hCaptcha iframe...")
    # Playwright: timeout in ms; 0 = disable (wait indefinitely)
    timeout_ms = int(timeout * 1000) if timeout else 0
    try:
        page.wait_for_selector("iframe[src*='hcaptcha.com']", timeout=timeout_ms)
        _log("hCaptcha iframe found")
    except PlaywrightTimeoutError:
        _log("Timeout: hCaptcha iframe did not appear")
        raise TimeoutError("hCaptcha iframe did not appear in time")


def _is_already_expanded(page: Page) -> bool:
    rect, _, _ = _get_viewport_and_crop(page)
    return rect is not None and rect.width >= MIN_SIZE and rect.height >= MIN_SIZE


def _wait_expanded(
    page: Page,
    timeout: Optional[float] = None,
) -> tuple[Optional[_CropRect], int, int]:
    _log("Waiting for captcha to expand (min %dx%d)..." % (MIN_SIZE, MIN_SIZE))
    deadline = (time.time() + timeout) if timeout is not None else None
    while True:
        rect, w, h = _get_viewport_and_crop(page)
        if rect is not None and rect.width >= MIN_SIZE and rect.height >= MIN_SIZE:
            _log("Captcha expanded: %dx%d at (%d, %d)" % (rect.width, rect.height, rect.left, rect.top))
            return rect, w, h
        if deadline is not None and time.time() >= deadline:
            _log("Timeout: captcha did not expand in time")
            raise TimeoutError("Captcha did not expand in time")
        time.sleep(1.0)


def _click_checkbox_iframe(page: Page) -> None:
    """Click at the center of the checkbox (small) iframe to expand the captcha."""
    result = page.evaluate("""() => {
        const iframes = document.querySelectorAll('iframe[src*="hcaptcha.com"]');
        for (const f of iframes) {
            const r = f.getBoundingClientRect();
            if (r.width >= 250 && r.height >= 250) continue;
            if (r.width >= 50 && r.height >= 50) {
                return { x: Math.round(r.left + r.width / 2), y: Math.round(r.top + r.height / 2) };
            }
        }
        return null;
    }""")
    if result:
        page.mouse.click(result["x"], result["y"])


def _open_checkbox_if_needed(
    page: Page,
    wait_captcha_timeout: Optional[float] = None,
    captcha_opens_automatically: bool = False,
) -> None:
    _wait_for_iframe(page, timeout=wait_captcha_timeout)
    time.sleep(1.2)
    if captcha_opens_automatically:
        _log("Captcha opens automatically; waiting for it to load (no checkbox click)")
        return
    if _is_already_expanded(page):
        _log("Captcha already expanded, skipping checkbox click")
        return
    _log("Clicking checkbox to expand captcha...")
    _click_checkbox_iframe(page)
    time.sleep(1.5)


def _get_token(page: Page) -> Optional[str]:
    try:
        val = page.evaluate("""() => {
            const el = document.querySelector('textarea[name="h-captcha-response"], input[name="h-captcha-response"]');
            return el ? (el.value || '').trim() : '';
        }""")
        return val or None
    except Exception:
        return None


def _run_loop(page: Page, api: RemoteSessionApiClient, task_id: str, crop: Optional[_CropRect]) -> None:
    last_shot = [time.perf_counter()]
    while True:
        try:
            resp = api.get_next_action(task_id)
            status = resp.get("status")
            if status in ("expired", "solved"):
                _log("Session ended: %s" % status)
                return
            action = resp.get("action")
            if isinstance(action, dict):
                atype = action.get("type")
                if atype == "click":
                    x, y = action.get("x"), action.get("y")
                    if x is not None and y is not None:
                        _log("Worker action: click (%d, %d)" % (int(x), int(y)))
                        page.mouse.click(int(x), int(y))
                        time.sleep(0.08)
                elif atype == "drag":
                    fr, to = action.get("from"), action.get("to")
                    if fr and to:
                        _log("Worker action: drag")
                        x1, y1 = int(fr["x"]), int(fr["y"])
                        x2, y2 = int(to["x"]), int(to["y"])
                        page.mouse.move(x1, y1)
                        page.mouse.down()
                        for i in range(1, 13):
                            t = i / 12.0
                            x = int(x1 + (x2 - x1) * t)
                            y = int(y1 + (y2 - y1) * t)
                            page.mouse.move(x, y)
                        page.mouse.up()
                        time.sleep(0.08)
            token = _get_token(page)
            if token:
                _log("Captcha solved, submitting token...")
                api.notify_solved(task_id, token)
                _log("Token submitted successfully")
                return
            now = time.perf_counter()
            if now - last_shot[0] >= SCREENSHOT_INTERVAL_S:
                try:
                    rect, w, h = _get_viewport_and_crop(page)
                    raw = page.screenshot()
                    b64 = base64.b64encode(raw).decode("ascii")
                    dto = CropRectDto(rect.left, rect.top, rect.width, rect.height) if rect else None
                    api.update_screenshot(task_id, "data:image/png;base64," + b64, w, h, dto)
                    last_shot[0] = now
                except Exception as e:
                    _log("Screenshot update error: %s" % e)
            time.sleep(POLL_S)
        except KeyboardInterrupt:
            _log("Interrupted by user")
            return
        except Exception as e:
            _log("Loop error: %s" % e)
            time.sleep(1.0)


def run_solve(
    page: Page,
    api: RemoteSessionApiClient,
    page_url: str,
    wait_captcha_timeout: Optional[float] = None,
    delay_after_captcha_load: float = 5.0,
    captcha_opens_automatically: bool = False,
) -> Optional[str]:
    """
    Run the full remote solve flow. Page must be on the URL with captcha.
    Returns task_id on success, None on failure.
    """
    _open_checkbox_if_needed(
        page,
        wait_captcha_timeout=wait_captcha_timeout,
        captcha_opens_automatically=captcha_opens_automatically,
    )
    crop, width, height = _wait_expanded(page, timeout=wait_captcha_timeout)
    if delay_after_captcha_load > 0:
        _log("Waiting %.1fs after captcha load before sending screenshot..." % delay_after_captcha_load)
        time.sleep(delay_after_captcha_load)
    _log("Creating task...")
    res = api.create_task(page_url)
    if res.get("errorId") != 0 or not res.get("taskId"):
        _log("Create task failed: errorId=%s %s" % (res.get("errorId"), res.get("errorDescription", "")))
        return None
    task_id = res["taskId"]
    _log("Task created: %s. Starting remote session..." % task_id)
    raw = page.screenshot()
    b64 = base64.b64encode(raw).decode("ascii")
    dto = CropRectDto(crop.left, crop.top, crop.width, crop.height) if crop else None
    api.start_remote_session(task_id, "data:image/png;base64," + b64, page_url, width, height, dto)
    _log("Waiting for worker to solve...")
    _run_loop(page, api, task_id, crop)
    return task_id
