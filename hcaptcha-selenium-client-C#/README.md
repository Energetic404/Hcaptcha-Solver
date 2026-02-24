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
