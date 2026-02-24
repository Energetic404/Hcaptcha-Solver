using System.Text.Json;
using OpenQA.Selenium;
using OpenQA.Selenium.Chrome;

namespace KenzxCaptcha.Remote;

/// <summary>
/// Remote hCaptcha solver client for captcha-platform / hcaptchasolver.com.
/// Use RunAsync to open a browser, load your page, and solve in one call; or use SolveAsync with your own WebDriver.
/// </summary>
public class RemoteCaptchaClient
{
    private const int PollMs = 120;
    private const int ScreenshotIntervalMs = 200;

    private readonly ApiClient _api;
    private readonly string _serverUrl;

    public RemoteCaptchaClient(string serverUrl, string apiKey)
    {
        _serverUrl = serverUrl.TrimEnd('/');
        _api = new ApiClient(_serverUrl, apiKey?.Trim() ?? "");
    }

    /// <summary>
    /// Solve the captcha using an existing WebDriver (must already be on a page with hCaptcha).
    /// </summary>
    /// <param name="driver">Your Selenium WebDriver (Chrome recommended).</param>
    /// <param name="pageUrl">URL of the current page (used when creating the remote task).</param>
    /// <param name="waitCaptchaTimeout">Max time to wait for captcha to appear and expand; null = wait indefinitely.</param>
    /// <param name="delayAfterCaptchaLoadSeconds">Seconds to wait after captcha is visible before sending first screenshot (default 5) to avoid null/blank screenshots.</param>
    /// <param name="captchaOpensAutomatically">If true, do not click the checkbox; the page opens the captcha (e.g. Discord). Library only waits for it to be visible and expanded.</param>
    /// <returns>Task ID if successful, null otherwise.</returns>
    public Task<string?> SolveAsync(
        IWebDriver driver,
        string pageUrl,
        TimeSpan? waitCaptchaTimeout,
        double delayAfterCaptchaLoadSeconds,
        bool captchaOpensAutomatically) =>
        SolveAsync(driver, pageUrl, waitCaptchaTimeout, delayAfterCaptchaLoadSeconds, captchaOpensAutomatically, default);

    public async Task<string?> SolveAsync(
        IWebDriver driver,
        string pageUrl = "https://accounts.hcaptcha.com/demo",
        TimeSpan? waitCaptchaTimeout = null,
        double delayAfterCaptchaLoadSeconds = 5.0,
        bool captchaOpensAutomatically = false,
        CancellationToken ct = default)
    {
        SolverHelper.OpenCaptchaCheckbox(driver, waitCaptchaTimeout, captchaOpensAutomatically);
        var (cropRect, width, height) = SolverHelper.WaitForCaptchaExpanded(driver, waitCaptchaTimeout);

        if (delayAfterCaptchaLoadSeconds > 0)
            await Task.Delay((int)(delayAfterCaptchaLoadSeconds * 1000), ct);

        var createTaskRes = await _api.CreateTaskAsync(pageUrl, ct);
        if (createTaskRes.ErrorId != 0 || string.IsNullOrEmpty(createTaskRes.TaskId))
            return null;

        var taskId = createTaskRes.TaskId;
        var screenshotBase64 = SolverHelper.TakeScreenshotBase64(driver);
        var dataUrl = "data:image/png;base64," + screenshotBase64;
        var cropDto = cropRect != null ? new CropRectDto(cropRect.Left, cropRect.Top, cropRect.Width, cropRect.Height) : null;
        await _api.StartRemoteSessionAsync(taskId, new CreateSessionRequest(dataUrl, pageUrl, width, height, cropDto), ct);

        var lastScreenshotTime = Environment.TickCount64;
        while (!ct.IsCancellationRequested)
        {
            try
            {
                var next = await _api.GetNextActionAsync(taskId, ct);
                if (next.Status == "expired" || next.Status == "solved")
                    return taskId;

                if (next.Action is { } actionEl && actionEl.ValueKind == JsonValueKind.Object)
                {
                    var type = actionEl.TryGetProperty("type", out var typeProp) ? typeProp.GetString() : null;
                    if (type == "click" && actionEl.TryGetProperty("x", out var xProp) && actionEl.TryGetProperty("y", out var yProp))
                    {
                        SolverHelper.PerformClick(driver, xProp.GetInt32(), yProp.GetInt32(), cropRect);
                        await Task.Delay(80, ct);
                    }
                    else if (type == "drag" && actionEl.TryGetProperty("from", out var fromEl) && actionEl.TryGetProperty("to", out var toEl))
                    {
                        var fromX = fromEl.GetProperty("x").GetInt32();
                        var fromY = fromEl.GetProperty("y").GetInt32();
                        var toX = toEl.GetProperty("x").GetInt32();
                        var toY = toEl.GetProperty("y").GetInt32();
                        SolverHelper.PerformDrag(driver, (fromX, fromY), (toX, toY), cropRect);
                        await Task.Delay(80, ct);
                    }
                }

                if (SolverHelper.IsCaptchaSolved(driver, out var token))
                {
                    await _api.NotifySolvedAsync(taskId, token, ct);
                    return taskId;
                }

                var now = Environment.TickCount64;
                if (now - lastScreenshotTime >= ScreenshotIntervalMs)
                {
                    try
                    {
                        var (rect, w, h) = SolverHelper.GetViewportAndCropRect(driver);
                        var b64 = SolverHelper.TakeScreenshotBase64(driver);
                        var crop = rect != null ? new CropRectDto(rect.Left, rect.Top, rect.Width, rect.Height) : null;
                        await _api.UpdateScreenshotAsync(taskId, new UpdateScreenshotRequest("data:image/png;base64," + b64, w, h, crop), ct);
                        lastScreenshotTime = now;
                    }
                    catch { }
                }

                await Task.Delay(PollMs, ct);
            }
            catch (OperationCanceledException)
            {
                return taskId;
            }
            catch
            {
                await Task.Delay(1000, ct);
            }
        }

        return taskId;
    }

    /// <summary>
    /// Launch Chrome, load the given page, wait for captcha, solve it remotely, then quit (or wait for Enter if keepBrowserOpen).
    /// </summary>
    /// <param name="pageUrl">URL to open (e.g. https://accounts.hcaptcha.com/demo or https://discord.com/register).</param>
    /// <param name="keepBrowserOpen">If true, wait for Enter after solve before closing (default true).</param>
    /// <param name="waitCaptchaTimeout">Max time to wait for captcha to appear; null = wait indefinitely.</param>
    /// <param name="delayAfterCaptchaLoadSeconds">Seconds to wait after captcha loads before first screenshot (default 5).</param>
    /// <param name="captchaOpensAutomatically">If true, do not click the checkbox; the page opens the captcha (e.g. Discord). Library only waits for it to be visible and expanded.</param>
    /// <returns>True if solved successfully.</returns>
    public Task<bool> RunAsync(
        string pageUrl,
        bool keepBrowserOpen,
        TimeSpan? waitCaptchaTimeout,
        double delayAfterCaptchaLoadSeconds,
        bool captchaOpensAutomatically) =>
        RunAsync(pageUrl, keepBrowserOpen, waitCaptchaTimeout, delayAfterCaptchaLoadSeconds, captchaOpensAutomatically, default);

    /// <summary>
    /// Launch Chrome, load the given page, wait for captcha, solve it remotely, then quit (or wait for Enter if keepBrowserOpen).
    /// </summary>
    public async Task<bool> RunAsync(
        string pageUrl = "https://accounts.hcaptcha.com/demo",
        bool keepBrowserOpen = true,
        TimeSpan? waitCaptchaTimeout = null,
        double delayAfterCaptchaLoadSeconds = 5.0,
        bool captchaOpensAutomatically = false,
        CancellationToken ct = default)
    {
        var options = new ChromeOptions();
        options.AddArgument("--disable-blink-features=AutomationControlled");
        options.AddExcludedArgument("enable-automation");
        options.AddArgument("--disable-dev-shm-usage");
        using var driver = new ChromeDriver(options);
        try
        {
            driver.Manage().Window.Size = new System.Drawing.Size(1280, 720);
            driver.Navigate().GoToUrl(pageUrl);
            var taskId = await SolveAsync(driver, pageUrl, waitCaptchaTimeout, delayAfterCaptchaLoadSeconds, captchaOpensAutomatically, ct);
            if (taskId == null)
                return false;
            if (keepBrowserOpen)
            {
                Console.WriteLine("Solved. Press Enter to close the browser...");
                Console.ReadLine();
            }
            return true;
        }
        catch
        {
            return false;
        }
    }
}
