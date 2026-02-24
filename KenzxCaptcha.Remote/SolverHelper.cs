using System.Text.Json;
using OpenQA.Selenium;
using OpenQA.Selenium.Interactions;
using OpenQA.Selenium.Support.UI;

namespace KenzxCaptcha.Remote;

internal static class SolverHelper
{
    internal const int MinCaptchaBoxSize = 260;

    /// <param name="timeout">Max time to wait; null = wait indefinitely.</param>
    internal static (CropRect? rect, int width, int height) WaitForCaptchaExpanded(IWebDriver driver, TimeSpan? timeout = null)
    {
        var maxWait = timeout ?? TimeSpan.FromSeconds(120);
        if (timeout == null)
        {
            while (true)
            {
                var (rect, w, h) = GetViewportAndCropRect(driver);
                if (rect != null && rect.Width >= MinCaptchaBoxSize && rect.Height >= MinCaptchaBoxSize)
                    return (rect, w, h);
                Thread.Sleep(1000);
            }
        }
        var wait = new WebDriverWait(driver, maxWait);
        wait.Until(d =>
        {
            var (rect, w, h) = GetViewportAndCropRect(d);
            return rect != null && rect.Width >= MinCaptchaBoxSize && rect.Height >= MinCaptchaBoxSize;
        });
        return GetViewportAndCropRect(driver);
    }

    /// <param name="timeout">Max time to wait for iframe; null = wait indefinitely.</param>
    /// <param name="captchaOpensAutomatically">If true, do not click the checkbox; page opens captcha (e.g. Discord). Only wait for iframe then return.</param>
    internal static void OpenCaptchaCheckbox(IWebDriver driver, TimeSpan? timeout = null, bool captchaOpensAutomatically = false)
    {
        var maxWait = timeout ?? TimeSpan.FromSeconds(15);
        if (timeout == null)
        {
            while (true)
            {
                var iframes = driver.FindElements(By.CssSelector("iframe[src*='hcaptcha.com']"));
                if (iframes.Count > 0) break;
                Thread.Sleep(1000);
            }
        }
        else
        {
            var wait = new WebDriverWait(driver, maxWait);
            wait.Until(d =>
            {
                var iframes = d.FindElements(By.CssSelector("iframe[src*='hcaptcha.com']"));
                return iframes.Count > 0;
            });
        }
        Thread.Sleep(800);
        if (captchaOpensAutomatically)
            return; // Page opens captcha; do not click. WaitForCaptchaExpanded will wait until it is visible.
        var iframes = driver.FindElements(By.CssSelector("iframe[src*='hcaptcha.com']"));
        IWebElement? checkboxFrame = null;
        foreach (var f in iframes)
        {
            var w = f.Size.Width;
            var h = f.Size.Height;
            if (w >= MinCaptchaBoxSize && h >= MinCaptchaBoxSize) continue;
            if (w >= 50 && h >= 50) { checkboxFrame = f; break; }
        }
        checkboxFrame ??= iframes[0];
        driver.SwitchTo().Frame(checkboxFrame);
        try
        {
            Thread.Sleep(300);
            var body = driver.FindElement(By.TagName("body"));
            var w2 = body.Size.Width;
            var h2 = body.Size.Height;
            var cx = Math.Max(15, w2 / 2 - 5);
            var cy = Math.Max(15, h2 / 2 - 5);
            new Actions(driver).MoveToElement(body, cx, cy).Click().Perform();
        }
        finally
        {
            driver.SwitchTo().DefaultContent();
        }
        Thread.Sleep(1500);
    }

    internal static (CropRect? rect, int width, int height) GetViewportAndCropRect(IWebDriver driver)
    {
        var script = """
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
            """;
        var raw = ((IJavaScriptExecutor)driver).ExecuteScript("return " + script.Trim() + ";");
        if (raw is not Dictionary<string, object> result)
        {
            return (null, 1280, 720);
        }
        var vw = GetInt(result, "viewportW", 1280);
        var vh = GetInt(result, "viewportH", 720);
        CropRect? rect = null;
        if (result.ContainsKey("left"))
        {
            rect = new CropRect(
                GetInt(result, "left", 0),
                GetInt(result, "top", 0),
                GetInt(result, "width", 0),
                GetInt(result, "height", 0));
        }
        return (rect, vw, vh);
    }

    internal static int GetInt(Dictionary<string, object> d, string key, int defaultValue)
    {
        if (!d.TryGetValue(key, out var v) || v == null) return defaultValue;
        return v switch
        {
            long n => (int)n,
            int n => n,
            double n => (int)n,
            _ => defaultValue
        };
    }

    internal static string TakeScreenshotBase64(IWebDriver driver)
    {
        var screenshot = ((ITakesScreenshot)driver).GetScreenshot();
        return screenshot.AsBase64EncodedString;
    }

    internal static void PerformClick(IWebDriver driver, int viewportX, int viewportY, CropRect? cropRect)
    {
        if (cropRect is { } r && IsInside(viewportX, viewportY, r))
        {
            var iframeX = viewportX - r.Left;
            var iframeY = viewportY - r.Top;
            ClickInFrame(driver, iframeX, iframeY);
        }
        else
        {
            ClickInMainPage(driver, viewportX, viewportY);
        }
    }

    internal static void PerformDrag(IWebDriver driver, (int x, int y) from, (int x, int y) to, CropRect? cropRect)
    {
        if (cropRect is { } r && IsInside(from.x, from.y, r) && IsInside(to.x, to.y, r))
        {
            var fromFx = from.x - r.Left;
            var fromFy = from.y - r.Top;
            var toFx = to.x - r.Left;
            var toFy = to.y - r.Top;
            DragInFrame(driver, (fromFx, fromFy), (toFx, toFy));
        }
        else
        {
            DragInMainPage(driver, from, to);
        }
    }

    internal static bool IsInside(int x, int y, CropRect r) =>
        x >= r.Left && x < r.Left + r.Width && y >= r.Top && y < r.Top + r.Height;

    internal static IWebElement GetLargestHcaptchaFrame(IWebDriver driver)
    {
        var iframes = driver.FindElements(By.CssSelector("iframe[src*='hcaptcha.com']"));
        IWebElement? best = null;
        var bestArea = 0;
        foreach (var f in iframes)
        {
            var w = f.Size.Width;
            var h = f.Size.Height;
            if (w < 50 || h < 50) continue;
            var area = w * h;
            if (area > bestArea) { bestArea = area; best = f; }
        }
        return best ?? driver.FindElement(By.CssSelector("iframe[src*='hcaptcha.com']"));
    }

    internal static void ClickInFrame(IWebDriver driver, int offsetX, int offsetY)
    {
        var iframe = GetLargestHcaptchaFrame(driver);
        driver.SwitchTo().Frame(iframe);
        try
        {
            SwitchToChallengeFrameIfAny(driver);
            Thread.Sleep(50);
            DispatchClickInCurrentFrame(driver, offsetX, offsetY);
        }
        finally
        {
            driver.SwitchTo().DefaultContent();
        }
    }

    internal static void SwitchToChallengeFrameIfAny(IWebDriver driver)
    {
        try
        {
            var inner = driver.FindElements(By.CssSelector("iframe"));
            foreach (var f in inner)
            {
                try
                {
                    driver.SwitchTo().Frame(f);
                    return;
                }
                catch { }
            }
        }
        catch { }
    }

    internal static void DispatchClickInCurrentFrame(IWebDriver driver, int x, int y)
    {
        var script = """
            (function(x, y) {
              var el = document.elementFromPoint(x, y);
              if (!el) return;
              ['mousedown', 'mouseup', 'click'].forEach(function(type) {
                el.dispatchEvent(new MouseEvent(type, { view: window, bubbles: true, cancelable: true, clientX: x, clientY: y, button: 0, buttons: type === 'mousedown' ? 1 : 0 }));
              });
            })(arguments[0], arguments[1]);
            """;
        ((IJavaScriptExecutor)driver).ExecuteScript(script, x, y);
    }

    internal static void ClickInMainPage(IWebDriver driver, int x, int y)
    {
        var body = driver.FindElement(By.TagName("body"));
        new Actions(driver)
            .MoveToElement(body, x, y)
            .Click()
            .Perform();
    }

    internal static void DragInFrame(IWebDriver driver, (int x, int y) from, (int x, int y) to)
    {
        var iframe = GetLargestHcaptchaFrame(driver);
        driver.SwitchTo().Frame(iframe);
        try
        {
            SwitchToChallengeFrameIfAny(driver);
            Thread.Sleep(50);
            DispatchDragInCurrentFrame(driver, from, to);
        }
        finally
        {
            driver.SwitchTo().DefaultContent();
        }
    }

    internal static void DispatchDragInCurrentFrame(IWebDriver driver, (int x, int y) from, (int x, int y) to)
    {
        var script = """
            (function(fx, fy, tx, ty) {
              var el = document.elementFromPoint(fx, fy);
              if (!el) return;
              el.dispatchEvent(new MouseEvent('mousedown', { view: window, bubbles: true, cancelable: true, clientX: fx, clientY: fy, button: 0, buttons: 1 }));
              var steps = 12;
              for (var i = 1; i <= steps; i++) {
                var t = i / steps;
                var x = Math.round(fx + (tx - fx) * t);
                var y = Math.round(fy + (ty - fy) * t);
                var target = document.elementFromPoint(x, y);
                (target || document.body).dispatchEvent(new MouseEvent('mousemove', { view: window, bubbles: true, cancelable: true, clientX: x, clientY: y, button: 0, buttons: 1 }));
              }
              var endEl = document.elementFromPoint(tx, ty);
              (endEl || document.body).dispatchEvent(new MouseEvent('mouseup', { view: window, bubbles: true, cancelable: true, clientX: tx, clientY: ty, button: 0, buttons: 0 }));
            })(arguments[0], arguments[1], arguments[2], arguments[3]);
            """;
        ((IJavaScriptExecutor)driver).ExecuteScript(script, from.x, from.y, to.x, to.y);
    }

    internal static void DragInMainPage(IWebDriver driver, (int x, int y) from, (int x, int y) to)
    {
        var body = driver.FindElement(By.TagName("body"));
        var actions = new Actions(driver);
        actions.MoveToElement(body, from.x, from.y).ClickAndHold().Perform();
        for (var i = 1; i <= 12; i++)
        {
            var t = i / 12.0;
            var x = (int)(from.x + (to.x - from.x) * t);
            var y = (int)(from.y + (to.y - from.y) * t);
            actions.MoveToElement(body, x, y).Perform();
        }
        actions.MoveToElement(body, to.x, to.y).Release().Perform();
    }

    internal static bool IsCaptchaSolved(IWebDriver driver, out string token)
    {
        token = "";
        try
        {
            var el = driver.FindElement(By.CssSelector("textarea[name='h-captcha-response'], input[name='h-captcha-response']"));
            var value = el.GetAttribute("value") ?? "";
            if (value.Length > 0)
            {
                token = value;
                return true;
            }
        }
        catch (NoSuchElementException) { }
        return false;
    }
}

internal record CropRect(int Left, int Top, int Width, int Height);
