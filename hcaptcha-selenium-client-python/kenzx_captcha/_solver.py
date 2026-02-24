from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException

from kenzx_captcha.api_client import _ApiClient, CropRectDto

if TYPE_CHECKING:
    from selenium.webdriver.remote.webdriver import WebDriver

MIN_SIZE = 260
POLL_S = 0.12
SCREENSHOT_INTERVAL_S = 0.2

_LOG_PREFIX = "[kenzx_captcha]"


def _log(msg: str) -> None:
    print(f"{_LOG_PREFIX} {msg}", flush=True)


@dataclass
class _CropRect:
    left: int
    top: int
    width: int
    height: int


def _get_viewport_and_crop(driver: WebDriver) -> tuple[Optional[_CropRect], int, int]:
    script = """
    (function() {
      var iframes = document.querySelectorAll('iframe[src*="hcaptcha.com"]');
      var best = null, bestArea = 0;
      for (var i = 0; i < iframes.length; i++) {
        var r = iframes[i].getBoundingClientRect();
        if (r.width < 50 || r.height < 50) continue;
        var area = r.width * r.height;
        if (area > bestArea) { bestArea = area; best = r; }
      }
      var w = window.innerWidth || 1280, h = window.innerHeight || 720;
      if (best) return { left: Math.round(best.left), top: Math.round(best.top), width: Math.round(best.width), height: Math.round(best.height), viewportW: w, viewportH: h };
      return { viewportW: w, viewportH: h };
    })()
    """
    result = driver.execute_script(f"return {script.strip()};")
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


def _wait_expanded(
    driver: WebDriver,
    timeout: Optional[float] = None,
) -> tuple[Optional[_CropRect], int, int]:
    """Wait until captcha iframe is expanded (big enough). timeout=None = wait indefinitely."""
    _log("Waiting for captcha to expand (min %dx%d)..." % (MIN_SIZE, MIN_SIZE))
    poll_interval = 1.0
    deadline = (time.time() + timeout) if timeout is not None else None
    while True:
        rect, w, h = _get_viewport_and_crop(driver)
        if rect is not None and rect.width >= MIN_SIZE and rect.height >= MIN_SIZE:
            _log("Captcha expanded: %dx%d at (%d, %d)" % (rect.width, rect.height, rect.left, rect.top))
            return rect, w, h
        if deadline is not None and time.time() >= deadline:
            _log("Timeout: captcha did not expand in time")
            raise TimeoutError("Captcha did not expand in time")
        time.sleep(poll_interval)


def _wait_for_iframe(driver: WebDriver, timeout: Optional[float] = None) -> None:
    """Wait until hCaptcha iframe is present. timeout=None = wait indefinitely."""
    _log("Waiting for hCaptcha iframe...")
    poll_interval = 1.0
    deadline = (time.time() + timeout) if timeout is not None else None
    while True:
        try:
            if driver.find_elements(By.CSS_SELECTOR, "iframe[src*='hcaptcha.com']"):
                _log("hCaptcha iframe found")
                return
        except Exception as e:
            _log("Check iframe error: %s" % e)
        if deadline is not None and time.time() >= deadline:
            _log("Timeout: hCaptcha iframe did not appear")
            raise TimeoutError("hCaptcha iframe did not appear in time")
        time.sleep(poll_interval)


def _is_already_expanded(driver: WebDriver) -> bool:
    rect, _, _ = _get_viewport_and_crop(driver)
    return rect is not None and rect.width >= MIN_SIZE and rect.height >= MIN_SIZE


def _click_checkbox_via_js(driver: WebDriver) -> None:
    """Click the checkbox using JS so it works when body has no size/location (e.g. Discord iframe)."""
    driver.execute_script("""
        var b = document.body;
        var x = 50, y = 50;
        ['mousedown', 'mouseup', 'click'].forEach(function(type) {
            b.dispatchEvent(new MouseEvent(type, { view: window, bubbles: true, cancelable: true, clientX: x, clientY: y, button: 0, buttons: type === 'mousedown' ? 1 : 0 }));
        });
    """)


def _open_checkbox_if_needed(
    driver: WebDriver,
    wait_captcha_timeout: Optional[float] = None,
    captcha_opens_automatically: bool = False,
) -> None:
    """
    Wait for iframe. Then either:
    - captcha_opens_automatically=True: do not click; just return (page will open captcha; use with _wait_expanded).
    - captcha_opens_automatically=False: if already expanded skip click, else click checkbox to expand.
    """
    _wait_for_iframe(driver, timeout=wait_captcha_timeout)
    time.sleep(1.2)
    if captcha_opens_automatically:
        _log("Captcha opens automatically on this page; waiting for it to load (no checkbox click)")
        return
    if _is_already_expanded(driver):
        _log("Captcha already expanded (e.g. Discord), skipping checkbox click")
        return
    _log("Clicking checkbox to expand captcha...")
    iframes = driver.find_elements(By.CSS_SELECTOR, "iframe[src*='hcaptcha.com']")
    checkbox_frame = None
    for f in iframes:
        w, h = f.size["width"], f.size["height"]
        if w >= MIN_SIZE and h >= MIN_SIZE:
            continue
        if w >= 50 and h >= 50:
            checkbox_frame = f
            break
    if checkbox_frame is None:
        checkbox_frame = iframes[0]
    driver.switch_to.frame(checkbox_frame)
    try:
        time.sleep(0.3)
        body = driver.find_element(By.TAG_NAME, "body")
        try:
            w2 = body.size.get("width", 0) if isinstance(body.size, dict) else getattr(body.size, "width", 0) or 0
            h2 = body.size.get("height", 0) if isinstance(body.size, dict) else getattr(body.size, "height", 0) or 0
        except Exception:
            w2, h2 = 0, 0
        if w2 < 10 or h2 < 10:
            _log("Checkbox iframe body has no size (e.g. Discord), using JS click")
            _click_checkbox_via_js(driver)
        else:
            cx, cy = max(15, w2 // 2 - 5), max(15, h2 // 2 - 5)
            try:
                ActionChains(driver).move_to_element_with_offset(body, cx, cy).click().perform()
            except ElementNotInteractableException:
                _log("ActionChains click failed (element not interactable), using JS click")
                _click_checkbox_via_js(driver)
    except ElementNotInteractableException:
        _log("Checkbox not interactable, using JS click")
        _click_checkbox_via_js(driver)
    finally:
        driver.switch_to.default_content()
    time.sleep(1.5)


def _inside(x: int, y: int, r: _CropRect) -> bool:
    return r.left <= x < r.left + r.width and r.top <= y < r.top + r.height


def _largest_frame(driver: WebDriver):
    iframes = driver.find_elements(By.CSS_SELECTOR, "iframe[src*='hcaptcha.com']")
    best = None
    best_area = 0
    for f in iframes:
        w, h = f.size["width"], f.size["height"]
        if w < 50 or h < 50:
            continue
        if w * h > best_area:
            best_area = w * h
            best = f
    return best if best else driver.find_element(By.CSS_SELECTOR, "iframe[src*='hcaptcha.com']")


def _switch_challenge_frame(driver: WebDriver) -> None:
    try:
        for f in driver.find_elements(By.CSS_SELECTOR, "iframe"):
            try:
                driver.switch_to.frame(f)
                return
            except Exception:
                pass
    except Exception:
        pass


def _click_in_frame(driver: WebDriver, ox: int, oy: int) -> None:
    driver.switch_to.frame(_largest_frame(driver))
    try:
        _switch_challenge_frame(driver)
        time.sleep(0.05)
        driver.execute_script("""
            (function(x, y) {
              var el = document.elementFromPoint(x, y);
              if (!el) return;
              ['mousedown', 'mouseup', 'click'].forEach(function(type) {
                el.dispatchEvent(new MouseEvent(type, { view: window, bubbles: true, cancelable: true, clientX: x, clientY: y, button: 0, buttons: type === 'mousedown' ? 1 : 0 }));
              });
            })(arguments[0], arguments[1]);
        """, ox, oy)
    finally:
        driver.switch_to.default_content()


def _click_main(driver: WebDriver, x: int, y: int) -> None:
    body = driver.find_element(By.TAG_NAME, "body")
    ActionChains(driver).move_to_element_with_offset(body, x, y).click().perform()


def _perform_click(driver: WebDriver, vx: int, vy: int, crop: Optional[_CropRect]) -> None:
    if crop and _inside(vx, vy, crop):
        _click_in_frame(driver, vx - crop.left, vy - crop.top)
    else:
        _click_main(driver, vx, vy)


def _drag_in_frame(driver: WebDriver, from_xy: tuple[int, int], to_xy: tuple[int, int]) -> None:
    fx, fy = from_xy
    tx, ty = to_xy
    driver.switch_to.frame(_largest_frame(driver))
    try:
        _switch_challenge_frame(driver)
        time.sleep(0.05)
        driver.execute_script("""
            (function(fx, fy, tx, ty) {
              var el = document.elementFromPoint(fx, fy);
              if (!el) return;
              el.dispatchEvent(new MouseEvent('mousedown', { view: window, bubbles: true, cancelable: true, clientX: fx, clientY: fy, button: 0, buttons: 1 }));
              for (var i = 1; i <= 12; i++) {
                var t = i / 12, x = Math.round(fx + (tx - fx) * t), y = Math.round(fy + (ty - fy) * t);
                (document.elementFromPoint(x, y) || document.body).dispatchEvent(new MouseEvent('mousemove', { view: window, bubbles: true, cancelable: true, clientX: x, clientY: y, button: 0, buttons: 1 }));
              }
              (document.elementFromPoint(tx, ty) || document.body).dispatchEvent(new MouseEvent('mouseup', { view: window, bubbles: true, cancelable: true, clientX: tx, clientY: ty, button: 0, buttons: 0 }));
            })(arguments[0], arguments[1], arguments[2], arguments[3]);
        """, fx, fy, tx, ty)
    finally:
        driver.switch_to.default_content()


def _drag_main(driver: WebDriver, from_xy: tuple[int, int], to_xy: tuple[int, int]) -> None:
    body = driver.find_element(By.TAG_NAME, "body")
    fx, fy = from_xy
    tx, ty = to_xy
    ActionChains(driver).move_to_element_with_offset(body, fx, fy).click_and_hold().perform()
    for i in range(1, 13):
        t = i / 12.0
        x, y = int(fx + (tx - fx) * t), int(fy + (ty - fy) * t)
        ActionChains(driver).move_to_element_with_offset(body, x, y).perform()
    ActionChains(driver).move_to_element_with_offset(body, tx, ty).release().perform()


def _perform_drag(driver: WebDriver, from_xy: tuple[int, int], to_xy: tuple[int, int], crop: Optional[_CropRect]) -> None:
    fx, fy = from_xy
    tx, ty = to_xy
    if crop and _inside(fx, fy, crop) and _inside(tx, ty, crop):
        _drag_in_frame(driver, (fx - crop.left, fy - crop.top), (tx - crop.left, ty - crop.top))
    else:
        _drag_main(driver, from_xy, to_xy)


def _get_token(driver: WebDriver) -> Optional[str]:
    try:
        el = driver.find_element(By.CSS_SELECTOR, "textarea[name='h-captcha-response'], input[name='h-captcha-response']")
        v = (el.get_attribute("value") or "").strip()
        return v or None
    except NoSuchElementException:
        return None


def _run_loop(driver: WebDriver, api: _ApiClient, task_id: str, crop: Optional[_CropRect]) -> None:
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
                        _perform_click(driver, int(x), int(y), crop)
                        time.sleep(0.08)
                elif atype == "drag":
                    fr, to = action.get("from"), action.get("to")
                    if fr and to:
                        _log("Worker action: drag")
                        _perform_drag(driver, (int(fr["x"]), int(fr["y"])), (int(to["x"]), int(to["y"])), crop)
                        time.sleep(0.08)
            token = _get_token(driver)
            if token:
                _log("Captcha solved, submitting token...")
                api.notify_solved(task_id, token)
                _log("Token submitted successfully")
                return
            now = time.perf_counter()
            if now - last_shot[0] >= SCREENSHOT_INTERVAL_S:
                try:
                    rect, w, h = _get_viewport_and_crop(driver)
                    b64 = driver.get_screenshot_as_base64()
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
    driver: WebDriver,
    api: _ApiClient,
    page_url: str,
    wait_captcha_timeout: Optional[float] = None,
    delay_after_captcha_load: float = 5.0,
    captcha_opens_automatically: bool = False,
) -> Optional[str]:
    """
    Run the full remote solve flow. Driver must be on the page with captcha already.
    wait_captcha_timeout: max seconds to wait for captcha to appear and expand; None = wait indefinitely.
    delay_after_captcha_load: seconds to wait after captcha is visible before sending first screenshot
        (default 5) to avoid null/blank screenshots while the widget is still rendering.
    captcha_opens_automatically: if True, do not click the checkbox; the page opens the captcha itself
        (e.g. Discord). Library only waits for the captcha to be visible and expanded.
    Returns task_id on success, None on failure.
    """
    _open_checkbox_if_needed(
        driver,
        wait_captcha_timeout=wait_captcha_timeout,
        captcha_opens_automatically=captcha_opens_automatically,
    )
    crop, width, height = _wait_expanded(driver, timeout=wait_captcha_timeout)
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
    b64 = driver.get_screenshot_as_base64()
    dto = CropRectDto(crop.left, crop.top, crop.width, crop.height) if crop else None
    api.start_remote_session(task_id, "data:image/png;base64," + b64, page_url, width, height, dto)
    _log("Waiting for worker to solve...")
    _run_loop(driver, api, task_id, crop)
    return task_id
