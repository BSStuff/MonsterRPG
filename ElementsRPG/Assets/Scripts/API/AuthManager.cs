using System;
using System.Collections;
using System.Text;
using Newtonsoft.Json;
using UnityEngine;
using UnityEngine.Networking;

/// <summary>
/// Singleton MonoBehaviour that manages authentication state.
/// Handles register, login, token refresh, and logout.
/// Persists JWT tokens in PlayerPrefs for session continuity.
/// </summary>
public class AuthManager : MonoBehaviour
{
    public static AuthManager Instance { get; private set; }

    private const string PrefKeyAccessToken = "auth_access_token";
    private const string PrefKeyRefreshToken = "auth_refresh_token";

    /// <summary>Current access token, read from PlayerPrefs.</summary>
    public string AccessToken => PlayerPrefs.GetString(PrefKeyAccessToken, null);

    /// <summary>Current refresh token, read from PlayerPrefs.</summary>
    public string RefreshTokenValue => PlayerPrefs.GetString(PrefKeyRefreshToken, null);

    /// <summary>True if an access token is stored.</summary>
    public bool IsLoggedIn => !string.IsNullOrEmpty(AccessToken);

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

    // ----------------------------------------------------------------
    // Login
    // ----------------------------------------------------------------

    /// <summary>
    /// Authenticates with email + password. On success, stores tokens and
    /// invokes onSuccess with the auth response.
    /// </summary>
    public void Login(
        string email, string password,
        Action<AuthResponse> onSuccess, Action<string> onError)
    {
        var body = new AuthRequest { Email = email, Password = password };
        StartCoroutine(PostAuth("/auth/login", body, onSuccess, onError));
    }

    // ----------------------------------------------------------------
    // Register
    // ----------------------------------------------------------------

    /// <summary>
    /// Creates a new account with email, password, and username.
    /// On success, stores tokens and invokes onSuccess.
    /// </summary>
    public void Register(
        string email, string password, string username,
        Action<AuthResponse> onSuccess, Action<string> onError)
    {
        var body = new RegisterRequest
        {
            Email = email,
            Password = password,
            Username = username
        };
        StartCoroutine(PostAuth("/auth/register", body, onSuccess, onError));
    }

    // ----------------------------------------------------------------
    // Token Refresh
    // ----------------------------------------------------------------

    /// <summary>
    /// Attempts to refresh the access token using the stored refresh token.
    /// Callback receives true on success, false on failure.
    /// On failure, stored tokens are cleared (user must re-login).
    /// </summary>
    public IEnumerator RefreshToken(Action<bool> callback)
    {
        string refreshToken = RefreshTokenValue;

        if (string.IsNullOrEmpty(refreshToken))
        {
            Debug.LogWarning("[AuthManager] No refresh token available.");
            callback?.Invoke(false);
            yield break;
        }

        string url = GetBaseUrl() + "/auth/refresh";
        var body = new RefreshRequest { RefreshToken = refreshToken };
        string json = JsonConvert.SerializeObject(body);

        using (UnityWebRequest request = new UnityWebRequest(url, "POST"))
        {
            byte[] bodyRaw = Encoding.UTF8.GetBytes(json);
            request.uploadHandler = new UploadHandlerRaw(bodyRaw);
            request.downloadHandler = new DownloadHandlerBuffer();
            request.SetRequestHeader("Content-Type", "application/json");

            yield return request.SendWebRequest();

            if (request.result == UnityWebRequest.Result.Success)
            {
                try
                {
                    var envelope = JsonConvert.DeserializeObject<ApiResponse<AuthResponse>>(
                        request.downloadHandler.text
                    );

                    if (envelope != null && envelope.Success && envelope.Data != null)
                    {
                        SaveTokens(envelope.Data);
                        Debug.Log("[AuthManager] Token refreshed successfully.");
                        callback?.Invoke(true);
                    }
                    else
                    {
                        Debug.LogWarning("[AuthManager] Refresh response was not successful.");
                        ClearTokens();
                        callback?.Invoke(false);
                    }
                }
                catch (Exception ex)
                {
                    Debug.LogError(
                        "[AuthManager] Failed to parse refresh response: " + ex.Message);
                    ClearTokens();
                    callback?.Invoke(false);
                }
            }
            else
            {
                Debug.LogWarning(
                    "[AuthManager] Token refresh failed: "
                    + request.responseCode + " " + request.error);
                ClearTokens();
                callback?.Invoke(false);
            }
        }
    }

    // ----------------------------------------------------------------
    // Logout
    // ----------------------------------------------------------------

    /// <summary>
    /// Clears stored tokens. Does not call any server endpoint.
    /// </summary>
    public void Logout()
    {
        ClearTokens();
        Debug.Log("[AuthManager] Logged out. Tokens cleared.");
    }

    // ----------------------------------------------------------------
    // Private Helpers
    // ----------------------------------------------------------------

    /// <summary>
    /// Shared coroutine for login and register -- both POST to an auth endpoint
    /// and return the same AuthResponse structure in the API envelope.
    /// </summary>
    private IEnumerator PostAuth(
        string path, object body,
        Action<AuthResponse> onSuccess, Action<string> onError)
    {
        string url = GetBaseUrl() + path;
        string json = JsonConvert.SerializeObject(body);

        using (UnityWebRequest request = new UnityWebRequest(url, "POST"))
        {
            byte[] bodyRaw = Encoding.UTF8.GetBytes(json);
            request.uploadHandler = new UploadHandlerRaw(bodyRaw);
            request.downloadHandler = new DownloadHandlerBuffer();
            request.SetRequestHeader("Content-Type", "application/json");

            yield return request.SendWebRequest();

            string responseBody = request.downloadHandler?.text;

            if (request.result == UnityWebRequest.Result.Success)
            {
                try
                {
                    var envelope =
                        JsonConvert.DeserializeObject<ApiResponse<AuthResponse>>(responseBody);

                    if (envelope != null && envelope.Success && envelope.Data != null)
                    {
                        SaveTokens(envelope.Data);
                        onSuccess?.Invoke(envelope.Data);
                    }
                    else
                    {
                        onError?.Invoke(
                            "Authentication failed: unexpected response format.");
                    }
                }
                catch (Exception ex)
                {
                    Debug.LogError(
                        "[AuthManager] Failed to parse auth response: " + ex.Message);
                    onError?.Invoke("Failed to parse server response: " + ex.Message);
                }
            }
            else
            {
                string errorMessage = ParseAuthError(responseBody, request);
                onError?.Invoke(errorMessage);
            }
        }
    }

    /// <summary>Saves access and refresh tokens to PlayerPrefs.</summary>
    private void SaveTokens(AuthResponse auth)
    {
        PlayerPrefs.SetString(PrefKeyAccessToken, auth.AccessToken);
        PlayerPrefs.SetString(PrefKeyRefreshToken, auth.RefreshToken);
        PlayerPrefs.Save();
    }

    /// <summary>Removes stored tokens from PlayerPrefs.</summary>
    private void ClearTokens()
    {
        PlayerPrefs.DeleteKey(PrefKeyAccessToken);
        PlayerPrefs.DeleteKey(PrefKeyRefreshToken);
        PlayerPrefs.Save();
    }

    /// <summary>
    /// Attempts to extract a user-friendly error message from the API error envelope.
    /// Falls back to the generic request error string.
    /// </summary>
    private string ParseAuthError(string responseBody, UnityWebRequest request)
    {
        if (!string.IsNullOrEmpty(responseBody))
        {
            try
            {
                var apiError = JsonConvert.DeserializeObject<ApiError>(responseBody);
                if (apiError?.Error != null
                    && !string.IsNullOrEmpty(apiError.Error.Message))
                {
                    return apiError.Error.Message;
                }
            }
            catch
            {
                // Fall through
            }
        }

        return !string.IsNullOrEmpty(request.error)
            ? request.error
            : "Authentication failed with status " + request.responseCode;
    }

    /// <summary>Gets the API base URL from GameConfig, with a fallback.</summary>
    private string GetBaseUrl()
    {
        return GameConfig.Instance != null
            ? GameConfig.Instance.ApiBaseUrl
            : "http://localhost:8000";
    }
}
