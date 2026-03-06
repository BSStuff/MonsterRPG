using System;
using System.Collections;
using System.Text;
using Newtonsoft.Json;
using UnityEngine;
using UnityEngine.Networking;

/// <summary>
/// Central HTTP client for all API communication.
/// Singleton MonoBehaviour that handles auth headers, JSON serialization,
/// response envelope unwrapping, and automatic 401 token refresh + retry.
/// All requests use UnityWebRequest + coroutines for WebGL compatibility.
/// </summary>
public class ApiClient : MonoBehaviour
{
    public static ApiClient Instance { get; private set; }

    private string BaseUrl => GameConfig.Instance != null
        ? GameConfig.Instance.ApiBaseUrl
        : "http://localhost:8000";

    private void Awake()
    {
        if (Instance != null && Instance != this)
        {
            Destroy(gameObject);
            return;
        }

        Instance = this;
        DontDestroyOnLoad(gameObject);
    }

    /// <summary>
    /// Convenience method so static API wrapper classes can start coroutines
    /// without being MonoBehaviours themselves.
    /// </summary>
    public void StartRequest(IEnumerator routine)
    {
        StartCoroutine(routine);
    }

    // ----------------------------------------------------------------
    // GET
    // ----------------------------------------------------------------

    /// <summary>
    /// Sends an authenticated GET request, deserializes the ApiResponse envelope,
    /// and returns the inner data via onSuccess callback.
    /// On 401, attempts one token refresh and retries.
    /// </summary>
    public IEnumerator Get<T>(
        string path, Action<T> onSuccess, Action<string> onError, bool isRetry = false)
    {
        string url = BaseUrl + path;

        using (UnityWebRequest request = UnityWebRequest.Get(url))
        {
            AttachAuthHeader(request);
            yield return request.SendWebRequest();

            if (request.responseCode == 401 && !isRetry)
            {
                yield return HandleUnauthorized<T>(
                    () => Get<T>(path, onSuccess, onError, true),
                    onError
                );
                yield break;
            }

            HandleResponse<T>(request, onSuccess, onError);
        }
    }

    // ----------------------------------------------------------------
    // POST with body
    // ----------------------------------------------------------------

    /// <summary>
    /// Sends an authenticated POST request with a JSON body.
    /// The body object is serialized via Newtonsoft.Json.
    /// </summary>
    public IEnumerator Post<T>(
        string path, object body, Action<T> onSuccess, Action<string> onError,
        bool isRetry = false)
    {
        string url = BaseUrl + path;
        string json = JsonConvert.SerializeObject(body);

        using (UnityWebRequest request = new UnityWebRequest(url, "POST"))
        {
            byte[] bodyRaw = Encoding.UTF8.GetBytes(json);
            request.uploadHandler = new UploadHandlerRaw(bodyRaw);
            request.downloadHandler = new DownloadHandlerBuffer();
            request.SetRequestHeader("Content-Type", "application/json");
            AttachAuthHeader(request);

            yield return request.SendWebRequest();

            if (request.responseCode == 401 && !isRetry)
            {
                yield return HandleUnauthorized<T>(
                    () => Post<T>(path, body, onSuccess, onError, true),
                    onError
                );
                yield break;
            }

            HandleResponse<T>(request, onSuccess, onError);
        }
    }

    // ----------------------------------------------------------------
    // POST without body
    // ----------------------------------------------------------------

    /// <summary>
    /// Sends an authenticated POST request with no body.
    /// Used for endpoints like /combat/{id}/round that take no request body.
    /// </summary>
    public IEnumerator PostNoBody<T>(
        string path, Action<T> onSuccess, Action<string> onError, bool isRetry = false)
    {
        string url = BaseUrl + path;

        using (UnityWebRequest request = new UnityWebRequest(url, "POST"))
        {
            request.downloadHandler = new DownloadHandlerBuffer();
            request.SetRequestHeader("Content-Type", "application/json");
            AttachAuthHeader(request);

            yield return request.SendWebRequest();

            if (request.responseCode == 401 && !isRetry)
            {
                yield return HandleUnauthorized<T>(
                    () => PostNoBody<T>(path, onSuccess, onError, true),
                    onError
                );
                yield break;
            }

            HandleResponse<T>(request, onSuccess, onError);
        }
    }

    // ----------------------------------------------------------------
    // POST with body (raw — no envelope unwrapping)
    // ----------------------------------------------------------------

    /// <summary>
    /// Sends an authenticated POST request with a JSON body and deserializes
    /// the response directly into T, bypassing the ApiResponse envelope.
    /// Use this for endpoints that return a flat response (e.g., POST /saves/).
    /// </summary>
    public IEnumerator PostRaw<T>(
        string path, object body, Action<T> onSuccess, Action<string> onError,
        bool isRetry = false)
    {
        string url = BaseUrl + path;
        string json = JsonConvert.SerializeObject(body);

        using (UnityWebRequest request = new UnityWebRequest(url, "POST"))
        {
            byte[] bodyRaw = Encoding.UTF8.GetBytes(json);
            request.uploadHandler = new UploadHandlerRaw(bodyRaw);
            request.downloadHandler = new DownloadHandlerBuffer();
            request.SetRequestHeader("Content-Type", "application/json");
            AttachAuthHeader(request);

            yield return request.SendWebRequest();

            if (request.responseCode == 401 && !isRetry)
            {
                yield return HandleUnauthorized<T>(
                    () => PostRaw<T>(path, body, onSuccess, onError, true),
                    onError
                );
                yield break;
            }

            HandleRawResponse<T>(request, onSuccess, onError);
        }
    }

    // ----------------------------------------------------------------
    // Helpers
    // ----------------------------------------------------------------

    /// <summary>
    /// Attaches the Bearer auth header if a token is available.
    /// </summary>
    private void AttachAuthHeader(UnityWebRequest request)
    {
        if (AuthManager.Instance != null && AuthManager.Instance.IsLoggedIn)
        {
            request.SetRequestHeader(
                "Authorization", "Bearer " + AuthManager.Instance.AccessToken);
        }
    }

    /// <summary>
    /// Attempts to refresh the auth token. If refresh succeeds, invokes the
    /// retry coroutine. If refresh fails, calls onError.
    /// </summary>
    private IEnumerator HandleUnauthorized<T>(
        Func<IEnumerator> retryFactory, Action<string> onError)
    {
        if (AuthManager.Instance == null)
        {
            onError?.Invoke("Authentication required but AuthManager is not available.");
            yield break;
        }

        bool refreshSucceeded = false;
        bool refreshComplete = false;

        AuthManager.Instance.StartCoroutine(
            AuthManager.Instance.RefreshToken(success =>
            {
                refreshSucceeded = success;
                refreshComplete = true;
            }));

        while (!refreshComplete)
        {
            yield return null;
        }

        if (refreshSucceeded)
        {
            yield return retryFactory();
        }
        else
        {
            onError?.Invoke("Session expired. Please log in again.");
        }
    }

    /// <summary>
    /// Parses the response body. On success (2xx), unwraps the ApiResponse envelope
    /// and invokes onSuccess with the data. On error, parses the error envelope
    /// and invokes onError with the message.
    /// </summary>
    private void HandleResponse<T>(
        UnityWebRequest request, Action<T> onSuccess, Action<string> onError)
    {
        string responseBody = request.downloadHandler?.text;

        if (request.result == UnityWebRequest.Result.Success)
        {
            try
            {
                var envelope = JsonConvert.DeserializeObject<ApiResponse<T>>(responseBody);

                if (envelope != null && envelope.Success)
                {
                    onSuccess?.Invoke(envelope.Data);
                }
                else
                {
                    onError?.Invoke("API returned success=false.");
                }
            }
            catch (Exception ex)
            {
                Debug.LogError(
                    "[ApiClient] Failed to deserialize response: " + ex.Message
                    + "\nBody: " + responseBody);
                onError?.Invoke("Failed to parse server response: " + ex.Message);
            }
        }
        else
        {
            string errorMessage = ParseErrorMessage(responseBody, request);
            Debug.LogWarning(
                "[ApiClient] Request failed: " + request.url
                + " -> " + request.responseCode + " " + errorMessage);
            onError?.Invoke(errorMessage);
        }
    }

    /// <summary>
    /// Parses the response body directly into T without unwrapping an envelope.
    /// Used by PostRaw for endpoints that return a flat JSON response.
    /// </summary>
    private void HandleRawResponse<T>(
        UnityWebRequest request, Action<T> onSuccess, Action<string> onError)
    {
        string responseBody = request.downloadHandler?.text;

        if (request.result == UnityWebRequest.Result.Success)
        {
            try
            {
                var result = JsonConvert.DeserializeObject<T>(responseBody);
                onSuccess?.Invoke(result);
            }
            catch (Exception ex)
            {
                Debug.LogError(
                    "[ApiClient] Failed to deserialize raw response: " + ex.Message
                    + "\nBody: " + responseBody);
                onError?.Invoke("Failed to parse server response: " + ex.Message);
            }
        }
        else
        {
            string errorMessage = ParseErrorMessage(responseBody, request);
            Debug.LogWarning(
                "[ApiClient] Request failed: " + request.url
                + " -> " + request.responseCode + " " + errorMessage);
            onError?.Invoke(errorMessage);
        }
    }

    /// <summary>
    /// Attempts to parse the API error envelope. Falls back to the raw error string
    /// from UnityWebRequest if parsing fails.
    /// </summary>
    private string ParseErrorMessage(string responseBody, UnityWebRequest request)
    {
        if (!string.IsNullOrEmpty(responseBody))
        {
            try
            {
                var apiError = JsonConvert.DeserializeObject<ApiError>(responseBody);
                if (apiError?.Error != null && !string.IsNullOrEmpty(apiError.Error.Message))
                {
                    return apiError.Error.Message;
                }
            }
            catch
            {
                // Fall through to generic error
            }
        }

        return !string.IsNullOrEmpty(request.error)
            ? request.error
            : "Request failed with status " + request.responseCode;
    }
}
