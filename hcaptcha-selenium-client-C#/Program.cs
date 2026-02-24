// Example: use KenzxCaptcha.Remote to solve hCaptcha remotely (short code).
//
// Usage: dotnet run -- [<serverUrl>] [<apiKey>]
//   Or set env: HCAPTCHA_SERVER_URL, HCAPTCHA_CLIENT_KEY
//
// Optional env (for remote run):
//   HCAPTCHA_PAGE_URL          - Page to open (default: https://accounts.hcaptcha.com/demo)
//   HCAPTCHA_WAIT_TIMEOUT_SEC  - Max seconds to wait for captcha (empty = wait forever)
//   HCAPTCHA_DELAY_AFTER_LOAD  - Seconds to wait after captcha loads before first screenshot (default: 5)
//   HCAPTCHA_KEEP_OPEN         - "0" or "false" to close browser immediately after solve
//   HCAPTCHA_OPENS_AUTOMATICALLY - "1" or "true" if the page opens the captcha (e.g. Discord). Library does not click checkbox, only waits for load.

using KenzxCaptcha.Remote;

var serverUrl = args.Length > 0 && args[0].StartsWith("http")
    ? args[0]
    : (Environment.GetEnvironmentVariable("HCAPTCHA_SERVER_URL") ?? "https://hcaptchasolver.com");

var clientKey = Environment.GetEnvironmentVariable("HCAPTCHA_CLIENT_KEY")?.Trim();
if (args.Length >= 2)
    clientKey = args[1];
else if (args.Length == 1 && !args[0].StartsWith("http"))
    clientKey = args[0];

if (string.IsNullOrWhiteSpace(clientKey))
{
    Console.WriteLine("Error: Set HCAPTCHA_CLIENT_KEY or pass: dotnet run -- [<serverUrl>] <apiKey>");
    return 1;
}

// Optional: page to open (e.g. Discord register or demo)
var pageUrl = Environment.GetEnvironmentVariable("HCAPTCHA_PAGE_URL") ?? "https://accounts.hcaptcha.com/demo";

// Optional: max seconds to wait for captcha (null = wait forever)
TimeSpan? waitTimeout = null;
if (int.TryParse(Environment.GetEnvironmentVariable("HCAPTCHA_WAIT_TIMEOUT_SEC") ?? "", out var sec) && sec > 0)
    waitTimeout = TimeSpan.FromSeconds(sec);

// Optional: delay after captcha loads before first screenshot (default 5 to avoid null screenshot)
var delayAfterLoad = 5.0;
if (double.TryParse(Environment.GetEnvironmentVariable("HCAPTCHA_DELAY_AFTER_LOAD") ?? "", out var d) && d >= 0)
    delayAfterLoad = d;

// Optional: keep browser open after solve
var keepOpen = true;
var keepStr = Environment.GetEnvironmentVariable("HCAPTCHA_KEEP_OPEN")?.Trim().ToLowerInvariant();
if (keepStr is "0" or "false")
    keepOpen = false;

// Optional: page opens captcha automatically (e.g. Discord). If true, we don't click checkbox, only wait for load.
var captchaOpensAuto = false;
var autoStr = Environment.GetEnvironmentVariable("HCAPTCHA_OPENS_AUTOMATICALLY")?.Trim().ToLowerInvariant();
if (autoStr is "1" or "true" or "yes")
    captchaOpensAuto = true;
if (pageUrl.Contains("discord.com", StringComparison.OrdinalIgnoreCase))
    captchaOpensAuto = true; // Discord opens captcha automatically

Console.WriteLine($"Server: {serverUrl}");
Console.WriteLine($"Page:   {pageUrl}");
var client = new RemoteCaptchaClient(serverUrl, clientKey);
// RunAsync(pageUrl, keepBrowserOpen) - use 2 args so it compiles. For timeout/delay/captchaOpensAutomatically use the full overload:
// await client.RunAsync(pageUrl, keepOpen, waitTimeout, delayAfterLoad, captchaOpensAuto);
var ok = await client.RunAsync(pageUrl, keepOpen);

return ok ? 0 : 1;
