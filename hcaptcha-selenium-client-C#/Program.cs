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
//
// Config: set env vars in the shell, or use a .env file in the app directory (copy .env.example to .env and edit).

using OpenQA.Selenium;
using OpenQA.Selenium.Chrome;
using KenzxCaptcha.Remote;

// Load .env file if present (sets environment variables from KEY=VALUE lines)
LoadEnvFile();

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

var options = new ChromeOptions();
options.AddArgument("--disable-blink-features=AutomationControlled");
options.AddExcludedArgument("enable-automation");
options.AddArgument("--disable-dev-shm-usage");
using var driver = new ChromeDriver(options);
driver.Manage().Window.Size = new System.Drawing.Size(1280, 720);
driver.Navigate().GoToUrl(pageUrl);

var taskId = await client.SolveAsync(driver, pageUrl, waitTimeout, delayAfterLoad, captchaOpensAuto);
var ok = taskId != null;

if (ok)
{
    // After captcha solved: click the demo submit button (hCaptcha demo page)
    try
    {
        var submit = driver.FindElement(By.XPath("//*[@id='hcaptcha-demo-submit']"));
        submit?.Click();
        Console.WriteLine("Clicked submit button.");
    }
    catch (NoSuchElementException)
    {
        try
        {
            var submit = driver.FindElement(By.XPath("/html/body/div[5]/form/fieldset/ul/li[3]/input"));
            submit?.Click();
            Console.WriteLine("Clicked submit button (full path).");
        }
        catch { /* page may not have the demo submit button */ }
    }
}

if (keepOpen)
{
    Console.WriteLine("Press Enter to close the browser...");
    Console.ReadLine();
}

return ok ? 0 : 1;

static void LoadEnvFile()
{
    // Prefer current directory (project folder when using dotnet run), then app base
    var envPath = Path.Combine(Directory.GetCurrentDirectory(), ".env");
    if (!File.Exists(envPath))
        envPath = Path.Combine(AppContext.BaseDirectory, ".env");
    if (!File.Exists(envPath))
        return;
    foreach (var line in File.ReadAllLines(envPath))
    {
        var s = line.Trim();
        if (s.Length == 0 || s[0] == '#') continue;
        var eq = s.IndexOf('=');
        if (eq <= 0) continue;
        var key = s[0..eq].Trim();
        var value = s[(eq + 1)..].Trim();
        if (value.Length >= 2 && value[0] == '"' && value[^1] == '"')
            value = value[1..^1].Replace("\\\"", "\"");
        if (string.IsNullOrEmpty(key)) continue;
        Environment.SetEnvironmentVariable(key, value, EnvironmentVariableTarget.Process);
    }
}
