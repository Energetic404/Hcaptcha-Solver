# hCaptcha remote solve — Playwright (Python) example

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Playwright](https://img.shields.io/badge/playwright-1.40+-green.svg)](https://playwright.dev/python/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Example script and helpers for [hcaptchasolver.com](https://hcaptchasolver.com) **remote captcha** solving using **Playwright** (Chromium) instead of Selenium. Open any page with hCaptcha; a worker solves it for you. Same platform API as the Selenium-based Python client.

---

## Features

- **Playwright** — Uses Playwright’s Chromium for browser automation (no Selenium/ChromeDriver).
- **Same remote flow** — Create task → send screenshot → worker sends click/drag → replay in browser → submit token.
- **Configurable** — Page URL, timeout, delay before first screenshot, “captcha opens automatically” (e.g. Discord), headless.

---

## Requirements

- **Python 3.9+**
- **Playwright** (Chromium; install browsers with `playwright install chromium`)
- **API key** from [hcaptchasolver.com](https://hcaptchasolver.com) (Dashboard → API Keys, format `Kenzx_...`)

---

## Install

```bash
cd hcaptcha-playwright-client-python
pip install -r requirements.txt
playwright install chromium
```

**Important:** After installing the Python packages, you must install Playwright’s browser binaries. Run `playwright install` (or `playwright install chromium` for Chromium only). Otherwise you’ll get an error like “Executable doesn’t exist”.

---

## Quick start

**1. Set your API key and run:**

Either use a `.env` file (copy `.env.example` to `.env` and set `HCAPTCHA_CLIENT_KEY`) or export the variable:

```bash
# Optional: copy .env.example to .env and set HCAPTCHA_CLIENT_KEY
export HCAPTCHA_CLIENT_KEY="Kenzx_YOUR_API_KEY"
python main.py
```

**2. Or pass server and key as arguments:**

```bash
python main.py https://hcaptchasolver.com Kenzx_YOUR_KEY
```

**3. Custom page (e.g. Discord):**

```bash
export HCAPTCHA_CLIENT_KEY="Kenzx_YOUR_KEY"
export HCAPTCHA_PAGE_URL="https://discord.com/register"
python main.py
```

---

## Environment variables

| Variable | Description |
|----------|-------------|
| `HCAPTCHA_SERVER_URL` | Base URL (default: `https://hcaptchasolver.com`). |
| `HCAPTCHA_CLIENT_KEY` | Your API key (required). |
| `HCAPTCHA_PAGE_URL` | Page to open (default: hCaptcha demo). |
| `HCAPTCHA_WAIT_TIMEOUT` | Max seconds to wait for captcha (empty = wait forever). |
| `HCAPTCHA_DELAY_AFTER_LOAD` | Seconds after captcha loads before first screenshot (default: 5). |
| `HCAPTCHA_OPENS_AUTOMATICALLY` | `1` or `true` if the page opens the captcha (e.g. Discord). |
| `HCAPTCHA_KEEP_OPEN` | `0` or `false` to close browser right after solve. |
| `HCAPTCHA_HEADLESS` | `1` or `true` to run Chromium headless. |

---

## Project layout

```
hcaptcha-playwright-client-python/
├── api_client.py          # Remote-session API (createTask, start, next-action, screenshot, solved)
├── solver_playwright.py   # Playwright solve flow (wait iframe, click checkbox, run loop)
├── main.py                # Example script
├── requirements.txt
├── README.md
├── LICENSE
└── .gitignore
```

---

## How it works

1. **Create task** — `POST /api/createTask` with `RemoteCaptchaTask` and optional `websiteURL`.
2. **Open page** — Playwright opens the URL and waits for the hCaptcha iframe.
3. **Expand captcha** — Optionally click the checkbox (or wait if the page opens it, e.g. Discord).
4. **Start session** — Send a screenshot and crop to the platform; a worker sees only the captcha.
5. **Loop** — Poll `next-action`; on click/drag, replay with `page.mouse`; send new screenshots until solved.
6. **Submit token** — When `h-captcha-response` is present, call `solved` → you’re charged, worker is paid.

Full API: [hcaptchasolver.com/api-docs](https://hcaptchasolver.com/api-docs).

---

## Selenium vs Playwright

This folder is a **standalone example** using Playwright. The **Selenium**-based client lives in `hcaptcha-selenium-client-python/` and is a full library (`kenzx_captcha`) with `run()` / `solve()` and optional undetected-Chrome. Use:

- **Playwright** — If you prefer Playwright, smaller deps, or already use it in your project.
- **Selenium** — If you want the packaged library, undetected Chrome, or the same API as the C# client.

Both talk to the same hcaptchasolver.com remote-session API.

---

## License

MIT — see [LICENSE](LICENSE).
