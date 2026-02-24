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

## License

MIT — see [LICENSE](../LICENSE) in the repository root.
