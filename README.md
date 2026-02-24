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
)
```

### `solve()` — use your own WebDriver

```python
from selenium import webdriver
from kenzx_captcha import RemoteCaptchaClient

driver = webdriver.Chrome()
driver.get("https://yoursite.com/login")

client = RemoteCaptchaClient("https://hcaptchasolver.com", "Kenzx_YOUR_KEY")
task_id = client.solve(
    driver,
    page_url=driver.current_url,
    wait_captcha_timeout=60,
    delay_after_captcha_load=5.0,
    captcha_opens_automatically=False,
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




# KenzxCaptcha.Remote

[![.NET 8](https://img.shields.io/badge/.NET-8.0-512BD4?logo=dotnet)](https://dotnet.microsoft.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](../LICENSE)

**.NET client library** for [hcaptchasolver.com](https://hcaptchasolver.com) **remote captcha** solving: open any page with hCaptcha in Chrome, and a worker solves it for you. Use `RunAsync()` for a one-line flow or `SolveAsync()` with your own WebDriver.

---

## Install

**Option A — Project reference (recommended)**

1. Clone or include the `KenzxCaptcha.Remote` folder in your solution.
2. Add a project reference:

   ```xml
   <ItemGroup>
     <ProjectReference Include="path\to\KenzxCaptcha.Remote\KenzxCaptcha.Remote.csproj" />
   </ItemGroup>
   ```

**Option B — Same repo as the example**

If you use the [HCaptchaSeleniumClient](https://github.com/YOUR_ORG/hcaptcha-selenium-client-csharp) example repo, the example already references this project. Clone the repo and open the solution.

---

## Quick start

```csharp
using KenzxCaptcha.Remote;

var client = new RemoteCaptchaClient(
    "https://hcaptchasolver.com",
    "Kenzx_YOUR_API_KEY"
);

// Opens Chrome, loads page, worker solves the captcha
var ok = await client.RunAsync(
    pageUrl: "https://accounts.hcaptcha.com/demo",
    keepBrowserOpen: true
);
```

---

## API

### `RunAsync` — library opens Chrome

```csharp
Task<bool> RunAsync(
    string pageUrl = "https://accounts.hcaptcha.com/demo",
    bool keepBrowserOpen = true,
    TimeSpan? waitCaptchaTimeout = null,
    double delayAfterCaptchaLoadSeconds = 5.0,
    bool captchaOpensAutomatically = false,
    CancellationToken ct = default
)
```

- **pageUrl** — Page to open.
- **keepBrowserOpen** — If true, waits for Enter after solve.
- **waitCaptchaTimeout** — Max time to wait for captcha; `null` = wait indefinitely.
- **delayAfterCaptchaLoadSeconds** — Seconds to wait after captcha is visible before first screenshot (default 5).
- **captchaOpensAutomatically** — If true, do not click the checkbox (e.g. Discord); only wait for captcha to load.

### `SolveAsync` — use your own WebDriver

```csharp
Task<string?> SolveAsync(
    IWebDriver driver,
    string pageUrl = "https://accounts.hcaptcha.com/demo",
    TimeSpan? waitCaptchaTimeout = null,
    double delayAfterCaptchaLoadSeconds = 5.0,
    bool captchaOpensAutomatically = false,
    CancellationToken ct = default
)
```

Returns the task ID when solved, or `null` on failure.

---

## Dependencies

- **Selenium.WebDriver** (4.21.0)
- **Selenium.Support** (4.21.0)
- **System.Text.Json** (8.0.5)

Target: **.NET 8.0**.

---




# hCaptcha Remote Solver — C# client & example

[![.NET 8](https://img.shields.io/badge/.NET-8.0-512BD4?logo=dotnet)](https://dotnet.microsoft.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

C# **example app** that uses the **KenzxCaptcha.Remote** library to solve hCaptcha remotely via [hcaptchasolver.com](https://hcaptchasolver.com): open any page with hCaptcha in Chrome, and a worker solves it for you.

---

## Repository layout

This repo is meant to be published **together with the library** so that one clone gives you both:

```
your-repo/
├── README.md                    (this file — at repo root)
├── LICENSE
├── .gitignore
├── KenzxCaptcha.Remote/         ← Library project
│   ├── KenzxCaptcha.Remote.csproj
│   ├── RemoteCaptchaClient.cs
│   ├── ApiClient.cs
│   ├── SolverHelper.cs
│   └── README.md
└── hcaptcha-selenium-client-C#/ ← Example app (this folder)
    ├── HCaptchaSeleniumClient.csproj
    └── Program.cs
```

The example’s `.csproj` references the library with `..\KenzxCaptcha.Remote\KenzxCaptcha.Remote.csproj`. If you use different folder names, update the `ProjectReference` path accordingly.

---

## Requirements

- **.NET 8.0 SDK**
- **Chrome** (for Selenium)
- **API key** from [hcaptchasolver.com](https://hcaptchasolver.com) (Dashboard → API Keys, format `Kenzx_...`)

---

## Build & run

**1. Restore and build**

From the **example app folder** (e.g. `hcaptcha-selenium-client-C#`):

```bash
dotnet restore
dotnet build
```

**2. Set your API key and run**

```powershell
$env:HCAPTCHA_CLIENT_KEY = "Kenzx_YOUR_API_KEY"
dotnet run
```

**With custom server and key as arguments:**

```bash
dotnet run -- https://hcaptchasolver.com Kenzx_YOUR_KEY
```

**Custom page (e.g. Discord):**

```powershell
$env:HCAPTCHA_PAGE_URL = "https://discord.com/register"
$env:HCAPTCHA_CLIENT_KEY = "Kenzx_YOUR_KEY"
dotnet run
```

---

## Example script — environment variables

| Variable | Description |
|----------|-------------|
| `HCAPTCHA_SERVER_URL` | Base URL (default: `https://hcaptchasolver.com`). |
| `HCAPTCHA_CLIENT_KEY` | Your API key (required). |
| `HCAPTCHA_PAGE_URL` | Page to open (default: hCaptcha demo). |
| `HCAPTCHA_WAIT_TIMEOUT_SEC` | Max seconds to wait for captcha (empty = forever). |
| `HCAPTCHA_DELAY_AFTER_LOAD` | Seconds after captcha loads before first screenshot (default: 5). |
| `HCAPTCHA_OPENS_AUTOMATICALLY` | `1` or `true` if the page opens the captcha (e.g. Discord). |
| `HCAPTCHA_KEEP_OPEN` | `0` or `false` to close browser right after solve. |

---

## Using the library in your own project

Add a project reference to **KenzxCaptcha.Remote**, then:

```csharp
using KenzxCaptcha.Remote;

var client = new RemoteCaptchaClient(
    "https://hcaptchasolver.com",
    "Kenzx_YOUR_API_KEY"
);

// Two-argument call (pageUrl, keepBrowserOpen)
var ok = await client.RunAsync("https://yoursite.com", keepBrowserOpen: true);

// With all options
var ok = await client.RunAsync(
    pageUrl: "https://discord.com/register",
    keepBrowserOpen: true,
    waitCaptchaTimeout: null,
    delayAfterCaptchaLoadSeconds: 5.0,
    captchaOpensAutomatically: true
);
```

See the [KenzxCaptcha.Remote README](../KenzxCaptcha.Remote/README.md) for full API (including `SolveAsync` with your own `IWebDriver`).

---

## How it works

1. The app opens Chrome and navigates to the page (e.g. demo or Discord).
2. It waits for the hCaptcha iframe and optionally clicks the checkbox to expand (or waits if the page opens it automatically).
3. It creates a **RemoteCaptchaTask** and starts a remote session with a screenshot and crop.
4. A **worker** at hcaptchasolver.com/worker sees the captcha and sends click/drag actions.
5. The app receives actions, replays them in the browser, and sends new screenshots until solved.
6. When the token is present, it submits it → you are charged, worker is paid.

Full API details: [hcaptchasolver.com/api-docs](https://hcaptchasolver.com/api-docs).

---

## License

MIT — see [LICENSE](LICENSE).
