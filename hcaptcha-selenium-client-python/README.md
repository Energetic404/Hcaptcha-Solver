# kenzx_captcha — Python client for hCaptcha remote solving

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Python client for [hcaptchasolver.com](https://hcaptchasolver.com) **remote captcha** flow: open any page with hCaptcha in a real browser, and a worker solves it for you. No proxy exposure — the worker never sees your proxy or full page.

---

## Features

- **One-line solve** — `client.run(page_url="https://yoursite.com")` opens the browser, waits for the captcha, and returns when solved.
- **Use your own driver** — `client.solve(driver, page_url=...)` with an existing Selenium WebDriver.
- **Configurable** — timeout, delay before first screenshot, “captcha opens automatically” (e.g. Discord), stable mode, headless.
- **Undetected Chrome** — uses `undetected-chromedriver` by default to reduce blocking on strict sites.

---

## Requirements

- **Python 3.9+**
- **Chrome** (browser)
- **API key** from [hcaptchasolver.com](https://hcaptchasolver.com) (Dashboard → API Keys, format `Kenzx_...`)

---

## Install

```bash
git clone https://github.com/YOUR_ORG/kenzx-captcha-python.git
cd kenzx-captcha-python
pip install -r requirements.txt
```

**Dependencies** (in `requirements.txt`):

- `selenium` — browser automation  
- `requests` — API calls  
- `undetected-chromedriver` — stealth Chrome (optional but recommended)

---

## Quick start

**1. Set your API key and run the example:**

```bash
export HCAPTCHA_CLIENT_KEY="Kenzx_YOUR_API_KEY"
python main.py
```

**2. Or in code:**

```python
from kenzx_captcha import RemoteCaptchaClient

client = RemoteCaptchaClient(
    "https://hcaptchasolver.com",
    "Kenzx_YOUR_API_KEY"
)

# Opens browser, loads page, worker solves the captcha
ok = client.run(
    page_url="https://accounts.hcaptcha.com/demo",
    keep_browser_open=True
)
```

---

## Usage

### `run()` — library opens the browser

```python
ok = client.run(
    page_url="https://yoursite.com/page-with-captcha",
    keep_browser_open=True,
    headless=False,
    use_undetected=True,
    stable_mode=None,                    # True for Discord/heavy sites
    wait_captcha_timeout=None,           # None = wait forever
    delay_after_captcha_load=5.0,        # Seconds before first screenshot (avoid blank)
    captcha_opens_automatically=False,   # True if page opens captcha (e.g. Discord)
    after_solve=None,                    # Optional callback(driver) after solve (e.g. click submit)
)
```

### `solve()` — use your own WebDriver

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from kenzx_captcha import RemoteCaptchaClient

driver = webdriver.Chrome()
driver.get("https://yoursite.com/login")

client = RemoteCaptchaClient("https://hcaptchasolver.com", "Kenzx_YOUR_KEY")
def click_submit(driver):
    driver.find_element(By.XPATH, "//*[@id='hcaptcha-demo-submit']").click()

task_id = client.solve(
    driver,
    page_url=driver.current_url,
    wait_captcha_timeout=60,
    delay_after_captcha_load=5.0,
    captcha_opens_automatically=False,
    after_solve=click_submit,  # optional: run action with driver after solve
)
# task_id when solved, None on failure
```

---

## Options

| Option | Description |
|--------|-------------|
| **page_url** | URL to open (or current page when using `solve()`). |
| **wait_captcha_timeout** | Max seconds to wait for captcha to appear. `None` = wait indefinitely. |
| **delay_after_captcha_load** | Seconds to wait after captcha is visible before sending the first screenshot (default `5`). Reduces null/blank screenshots. |
| **captcha_opens_automatically** | If `True`, the library does **not** click the checkbox; the page opens the captcha (e.g. Discord). Library only waits for it to load. |
| **after_solve** | Optional `callback(driver)` run after a successful solve (e.g. click submit button). Use with `run()` or `solve()`. |
| **stable_mode** | (Python) Chrome flags to reduce crashes on heavy sites (e.g. Discord). Auto-enabled when `page_url` contains `discord.com`. |
| **keep_browser_open** | If `True`, browser stays open after solve until you press Enter. |
| **headless** | Run browser in headless mode. |
| **use_undetected** | Use `undetected-chromedriver` (default `True`). |

---

## Example script — environment variables

`main.py` supports:

| Variable | Description |
|----------|-------------|
| `HCAPTCHA_SERVER_URL` | Base URL (default: `https://hcaptchasolver.com`). |
| `HCAPTCHA_CLIENT_KEY` | Your API key (required). |
| `HCAPTCHA_PAGE_URL` | Page to open (default: hCaptcha demo). |
| `HCAPTCHA_WAIT_TIMEOUT` | Max seconds to wait for captcha (empty = forever). |
| `HCAPTCHA_DELAY_AFTER_LOAD` | Seconds after captcha loads before first screenshot (default: 5). |
| `HCAPTCHA_OPENS_AUTOMATICALLY` | `1` or `true` if the page opens the captcha (e.g. Discord). |
| `HCAPTCHA_STABLE_MODE` | `1` or `true` for stable mode. |
| `HCAPTCHA_KEEP_OPEN` | `0` or `false` to close browser right after solve. |
| `HCAPTCHA_CLICK_SUBMIT_AFTER_SOLVE` | `1` or `true` to click the submit button after solve (e.g. demo page `#hcaptcha-demo-submit`). |
| `HCAPTCHA_HEADLESS` | `1` or `true` for headless. |

**Run with custom page (e.g. Discord):**

```bash
export HCAPTCHA_CLIENT_KEY="Kenzx_YOUR_KEY"
export HCAPTCHA_PAGE_URL="https://discord.com/register"
python main.py
```

**Or pass server and key as arguments:**

```bash
python main.py https://hcaptchasolver.com Kenzx_YOUR_KEY
```

---

## How it works

1. You create a **RemoteCaptchaTask** (or the library does via the platform API).
2. Your app opens the page in Chrome and waits for the hCaptcha iframe.
3. The library optionally clicks the checkbox to expand the captcha (or waits if it opens automatically).
4. It sends a screenshot and crop to the platform; a **worker** sees only the captcha and solves it (click/drag).
5. The library receives actions, replays them in your browser, and sends new screenshots until solved.
6. When the token is present, it submits it → you are charged, worker is paid.

Full API details: [hcaptchasolver.com/api-docs](https://hcaptchasolver.com/api-docs).

---

## License

MIT — see [LICENSE](LICENSE).
