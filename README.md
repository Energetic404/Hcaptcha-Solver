# Hcaptcha-Solver — Client libraries & examples

[![.NET 8](https://img.shields.io/badge/.NET-8.0-512BD4?logo=dotnet)](https://dotnet.microsoft.com/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Playwright](https://img.shields.io/badge/playwright-1.40+-green.svg)](https://playwright.dev/python/)

Client libraries and example apps for **[hcaptchasolver.com](https://hcaptchasolver.com)** **remote captcha** solving: open any page with hCaptcha in a real browser (Chrome), and a worker solves it for you. One repo contains the **C# library**, the **C# example app**, the **Python client** (Selenium, library + example), and a **Python Playwright example**.

---

## What’s in this repo

| Path | Description |
|------|-------------|
| **`KenzxCaptcha.Remote/`** | .NET 8 **library** — use in your C# app to solve hCaptcha remotely. |
| **`hcaptcha-selenium-client-C#/`** | C# **example app** — console app that uses the library; run as-is or copy patterns. |
| **`hcaptcha-selenium-client-python/`** | Python **library + example** — `kenzx_captcha` package (Selenium) and `main.py` demo. |
| **`hcaptcha-playwright-client-python/`** | Python **Playwright example** — same remote flow using Playwright (Chromium) instead of Selenium. |

All of them talk to the same platform: you get an API key from [hcaptchasolver.com](https://hcaptchasolver.com), open a page with hCaptcha, and a worker solves it remotely (you never expose your proxy; the worker only sees the captcha area).

---

## Quick start

### C# (library + example)

**Requirements:** .NET 8.0 SDK, Chrome, API key from [hcaptchasolver.com](https://hcaptchasolver.com) (format `Kenzx_...`).

```powershell
cd "hcaptcha-selenium-client-C#"
dotnet restore
dotnet build

$env:HCAPTCHA_CLIENT_KEY = "Kenzx_YOUR_API_KEY"
dotnet run
```

Or pass server and key as arguments:

```bash
dotnet run -- https://hcaptchasolver.com Kenzx_YOUR_KEY
```

**Use the library in your own project:** add a project reference to `KenzxCaptcha.Remote` and see [KenzxCaptcha.Remote/README.md](KenzxCaptcha.Remote/README.md).

---

### Python (library + example)

**Requirements:** Python 3.9+, Chrome, API key from [hcaptchasolver.com](https://hcaptchasolver.com) (format `Kenzx_...`).

```bash
cd hcaptcha-selenium-client-python
pip install -r requirements.txt

export HCAPTCHA_CLIENT_KEY="Kenzx_YOUR_API_KEY"
python main.py
```

Or pass server and key as arguments:

```bash
python main.py https://hcaptchasolver.com Kenzx_YOUR_KEY
```

**Use the library in your own code:** import `kenzx_captcha` from this folder or install it; see [hcaptcha-selenium-client-python/README.md](hcaptcha-selenium-client-python/README.md).

---

### Python (Playwright example)

**Requirements:** Python 3.9+, Playwright (Chromium), API key from [hcaptchasolver.com](https://hcaptchasolver.com) (format `Kenzx_...`).

```bash
cd hcaptcha-playwright-client-python
pip install -r requirements.txt
playwright install chromium

export HCAPTCHA_CLIENT_KEY="Kenzx_YOUR_API_KEY"
python main.py
```

Or pass server and key as arguments:

```bash
python main.py https://hcaptchasolver.com Kenzx_YOUR_KEY
```

**Details:** [hcaptcha-playwright-client-python/README.md](hcaptcha-playwright-client-python/README.md).

---

## Repository layout

```
Hcaptcha-Solver/
├── README.md                         ← You are here
├── LICENSE
│
├── KenzxCaptcha.Remote/              ← C# library
│   ├── KenzxCaptcha.Remote.csproj
│   ├── RemoteCaptchaClient.cs
│   ├── ApiClient.cs
│   ├── SolverHelper.cs
│   └── README.md
│
├── hcaptcha-selenium-client-C#/      ← C# example app
│   ├── HCaptchaSeleniumClient.csproj  (references ../KenzxCaptcha.Remote)
│   ├── Program.cs
│   ├── .env.example
│   └── README.md
│
├── hcaptcha-selenium-client-python/  ← Python library + example (Selenium)
│   ├── kenzx_captcha/                 (package: client, api_client, _solver)
│   ├── main.py                        (example script)
│   ├── requirements.txt
│   ├── README.md
│   └── LICENSE
│
└── hcaptcha-playwright-client-python/  ← Python example (Playwright)
    ├── api_client.py                  (remote-session API)
    ├── solver_playwright.py            (solve flow)
    ├── main.py                        (example script)
    ├── requirements.txt
    ├── README.md
    └── LICENSE
```

---

## C# — Library (KenzxCaptcha.Remote)

- **Target:** .NET 8.0  
- **Dependencies:** Selenium.WebDriver, Selenium.Support, System.Text.Json  

**Two ways to use it:**

1. **`RunAsync()`** — library opens Chrome, loads the page, waits for the captcha, solves it, then optionally keeps the browser open.
2. **`SolveAsync(driver, ...)`** — you provide your own `IWebDriver`; library only handles the solve flow (e.g. for custom navigation or post-solve actions like clicking submit).

**Quick example:**

```csharp
using KenzxCaptcha.Remote;

var client = new RemoteCaptchaClient(
    "https://hcaptchasolver.com",
    "Kenzx_YOUR_API_KEY"
);

// Library opens browser and solves
var ok = await client.RunAsync(
    pageUrl: "https://accounts.hcaptcha.com/demo",
    keepBrowserOpen: true
);

// Or use your own driver and e.g. click submit after solve
// var taskId = await client.SolveAsync(driver, pageUrl, ...);
```

**Options:** `pageUrl`, `keepBrowserOpen`, `waitCaptchaTimeout` (null = wait forever), `delayAfterCaptchaLoadSeconds` (default 5), `captchaOpensAutomatically` (e.g. Discord).  
Full API: [KenzxCaptcha.Remote/README.md](KenzxCaptcha.Remote/README.md).

---

## C# — Example app (hcaptcha-selenium-client-C#)

- Builds and runs the library’s flow: opens Chrome, loads a page (default: hCaptcha demo), waits for captcha, worker solves it, then optionally clicks the demo submit button and keeps the browser open.
- **Config:** environment variables or `.env` file (see `.env.example`); or command-line args: `dotnet run -- [<serverUrl>] [<apiKey>]`.

| Variable | Description |
|----------|-------------|
| `HCAPTCHA_SERVER_URL` | Base URL (default: `https://hcaptchasolver.com`). |
| `HCAPTCHA_CLIENT_KEY` | Your API key (required). |
| `HCAPTCHA_PAGE_URL` | Page to open (default: hCaptcha demo). |
| `HCAPTCHA_WAIT_TIMEOUT_SEC` | Max seconds to wait for captcha (empty = forever). |
| `HCAPTCHA_DELAY_AFTER_LOAD` | Seconds after captcha loads before first screenshot (default: 5). |
| `HCAPTCHA_OPENS_AUTOMATICALLY` | `1` or `true` if the page opens the captcha (e.g. Discord). |
| `HCAPTCHA_KEEP_OPEN` | `0` or `false` to close browser right after solve. |

More: [hcaptcha-selenium-client-C#/README.md](hcaptcha-selenium-client-C%23/README.md).

---

## Python — Library & example (hcaptcha-selenium-client-python)

- **Package:** `kenzx_captcha` (use `RemoteCaptchaClient`, optional `create_driver`).
- **Example:** `main.py` — same flow as the C# example, configurable via env vars or args.

**Two ways to use the library:**

1. **`run()`** — library opens the browser, loads the page, waits for the captcha, solves it, then optionally runs an `after_solve(driver)` callback and keeps the browser open.
2. **`solve(driver, ...)`** — you provide your own WebDriver; library handles the solve flow; you can pass `after_solve` to e.g. click a submit button.

**Quick example:**

```python
from kenzx_captcha import RemoteCaptchaClient

client = RemoteCaptchaClient(
    "https://hcaptchasolver.com",
    "Kenzx_YOUR_API_KEY"
)

# Library opens browser and solves
ok = client.run(
    page_url="https://accounts.hcaptcha.com/demo",
    keep_browser_open=True
)

# Or use your own driver and e.g. click submit after solve
# task_id = client.solve(driver, page_url=..., after_solve=click_submit)
```

**Options:** `page_url`, `keep_browser_open`, `wait_captcha_timeout` (None = wait forever), `delay_after_captcha_load` (default 5), `captcha_opens_automatically` (e.g. Discord), `after_solve` (callback(driver)), `stable_mode`, `headless`, `use_undetected`.  

**Example script env vars:** same as C# plus `HCAPTCHA_STABLE_MODE`, `HCAPTCHA_CLICK_SUBMIT_AFTER_SOLVE`, `HCAPTCHA_HEADLESS`.  
Full docs: [hcaptcha-selenium-client-python/README.md](hcaptcha-selenium-client-python/README.md).

---

## Python — Playwright example (hcaptcha-playwright-client-python)

- **Same remote flow** as the Selenium client, but uses **Playwright** (Chromium) for browser automation.
- **Standalone example** — `api_client.py`, `solver_playwright.py`, and `main.py`; no separate package.
- **Config:** env vars (e.g. `HCAPTCHA_CLIENT_KEY`, `HCAPTCHA_PAGE_URL`, `HCAPTCHA_HEADLESS`) or CLI args.

**Quick start:** `pip install -r requirements.txt && playwright install chromium`, then `export HCAPTCHA_CLIENT_KEY="Kenzx_..." && python main.py`.  
Full docs: [hcaptcha-playwright-client-python/README.md](hcaptcha-playwright-client-python/README.md).

---

## How it works (all clients)

1. You (or the library) create a **RemoteCaptchaTask** via the platform API.
2. Your app opens the page in Chrome and waits for the hCaptcha iframe.
3. The library optionally clicks the checkbox to expand the captcha (or waits if the page opens it automatically, e.g. Discord).
4. It sends a screenshot and crop to the platform; a **worker** at hcaptchasolver.com sees only the captcha and sends click/drag actions.
5. The client receives actions, replays them in the browser, and sends new screenshots until the captcha is solved.
6. When the token is present, it’s submitted → you’re charged, the worker is paid.

Full API and task types: [hcaptchasolver.com/api-docs](https://hcaptchasolver.com/api-docs).

---

## Requirements summary

| | C# | Python (Selenium) | Python (Playwright) |
|---|----|--------|--------|
| **Runtime** | .NET 8.0 SDK | Python 3.9+ | Python 3.9+ |
| **Browser** | Chrome | Chrome | Chromium (Playwright) |
| **API key** | From [hcaptchasolver.com](https://hcaptchasolver.com) (Dashboard → API Keys) | Same | Same |

---

## License

MIT — see [LICENSE](LICENSE) in the repository root.
