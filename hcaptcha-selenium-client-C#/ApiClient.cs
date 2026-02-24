using System.Net.Http.Json;
using System.Text;
using System.Text.Json;

namespace HCaptchaSeleniumClient;

/// <summary>API client for the captcha-platform at hcaptchasolver.com (createTask + remote-session flow).</summary>
public class ApiClient
{
    private readonly HttpClient _http;
    private readonly string _baseUrl;
    private readonly string _clientKey;
    private static readonly JsonSerializerOptions JsonOptions = new() { PropertyNamingPolicy = JsonNamingPolicy.CamelCase };

    public ApiClient(string baseUrl, string clientKey)
    {
        _baseUrl = baseUrl.TrimEnd('/');
        _clientKey = clientKey ?? "";
        _http = new HttpClient { BaseAddress = new Uri(_baseUrl) };
        _http.DefaultRequestHeaders.Add("Cache-Control", "no-store");
    }

    /// <summary>Create a RemoteCaptchaTask; returns taskId to use for the remote session.</summary>
    public async Task<CreateTaskResponse> CreateTaskAsync(string? pageUrl = null, CancellationToken ct = default)
    {
        var body = new
        {
            clientKey = _clientKey,
            task = new
            {
                type = "RemoteCaptchaTask",
                websiteURL = pageUrl ?? "https://accounts.hcaptcha.com/demo"
            }
        };
        var json = JsonSerializer.Serialize(body, JsonOptions);
        var content = new StringContent(json, Encoding.UTF8, "application/json");
        var res = await _http.PostAsync("/api/createTask", content, ct);
        res.EnsureSuccessStatusCode();
        var result = await res.Content.ReadFromJsonAsync<CreateTaskResponse>(new JsonSerializerOptions { PropertyNameCaseInsensitive = true }, ct);
        return result ?? throw new InvalidOperationException("Empty response");
    }

    /// <summary>Start remote session for the given taskId (screenshot, pageUrl, dimensions).</summary>
    public async Task<StartSessionResponse> StartRemoteSessionAsync(string taskId, CreateSessionRequest request, CancellationToken ct = default)
    {
        var body = new
        {
            clientKey = _clientKey,
            taskId,
            screenshot = request.Screenshot,
            pageUrl = request.PageUrl,
            width = request.Width,
            height = request.Height,
            cropRect = request.CropRect
        };
        var json = JsonSerializer.Serialize(body, JsonOptions);
        var content = new StringContent(json, Encoding.UTF8, "application/json");
        var res = await _http.PostAsync("/api/client/remote-session/start", content, ct);
        res.EnsureSuccessStatusCode();
        return await res.Content.ReadFromJsonAsync<StartSessionResponse>(new JsonSerializerOptions { PropertyNameCaseInsensitive = true }, ct)
            ?? new StartSessionResponse();
    }

    /// <summary>Poll for next click/drag action from the worker.</summary>
    public async Task<NextActionResponse> GetNextActionAsync(string taskId, CancellationToken ct = default)
    {
        var url = $"/api/client/remote-session/{taskId}/next-action?clientKey={Uri.EscapeDataString(_clientKey)}";
        var res = await _http.GetAsync(url, ct);
        res.EnsureSuccessStatusCode();
        var result = await res.Content.ReadFromJsonAsync<NextActionResponse>(new JsonSerializerOptions { PropertyNameCaseInsensitive = true }, ct);
        return result ?? throw new InvalidOperationException("Empty response");
    }

    /// <summary>Send updated screenshot after performing an action.</summary>
    public async Task UpdateScreenshotAsync(string taskId, UpdateScreenshotRequest request, CancellationToken ct = default)
    {
        var body = new
        {
            clientKey = _clientKey,
            screenshot = request.Screenshot,
            width = request.Width,
            height = request.Height,
            cropRect = request.CropRect
        };
        var json = JsonSerializer.Serialize(body, JsonOptions);
        var content = new StringContent(json, Encoding.UTF8, "application/json");
        var res = await _http.PostAsync($"/api/client/remote-session/{taskId}/screenshot", content, ct);
        res.EnsureSuccessStatusCode();
    }

    /// <summary>Notify that the captcha was solved and submit the token (worker gets credit, client is charged).</summary>
    public async Task NotifySolvedAsync(string taskId, string token, CancellationToken ct = default)
    {
        var body = new { clientKey = _clientKey, token };
        var json = JsonSerializer.Serialize(body, JsonOptions);
        var content = new StringContent(json, Encoding.UTF8, "application/json");
        var res = await _http.PostAsync($"/api/client/remote-session/{taskId}/solved", content, ct);
        res.EnsureSuccessStatusCode();
    }

    public async Task NotifyExpiredAsync(string taskId, CancellationToken ct = default)
    {
        // Platform does not have an expire endpoint; task will timeout by cleanup. No-op.
        await Task.CompletedTask;
    }
}

public record CreateSessionRequest(string? Screenshot, string PageUrl, int Width, int Height, CropRectDto? CropRect);

public record CropRectDto(int Left, int Top, int Width, int Height);

public class CreateTaskResponse
{
    [System.Text.Json.Serialization.JsonPropertyName("errorId")]
    public int ErrorId { get; set; }
    [System.Text.Json.Serialization.JsonPropertyName("taskId")]
    public string? TaskId { get; set; }
    [System.Text.Json.Serialization.JsonPropertyName("errorDescription")]
    public string? ErrorDescription { get; set; }
}

public class StartSessionResponse
{
    [System.Text.Json.Serialization.JsonPropertyName("sessionId")]
    public string? SessionId { get; set; }
    [System.Text.Json.Serialization.JsonPropertyName("message")]
    public string? Message { get; set; }
}

public class NextActionResponse
{
    public JsonElement? Action { get; set; }
    public string? Status { get; set; }
}

public record UpdateScreenshotRequest(string Screenshot, int Width, int Height, CropRectDto? CropRect);
