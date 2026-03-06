using System.Collections;
using Newtonsoft.Json.Linq;
using UnityEngine;
using UnityEngine.Networking;

/// <summary>
/// Singleton that loads runtime configuration from StreamingAssets/config.json.
/// Must be placed on a GameObject in the first loaded scene.
/// Uses UnityWebRequest for WebGL compatibility (File.ReadAllText does not work in WebGL).
/// </summary>
public class GameConfig : MonoBehaviour
{
    public static GameConfig Instance { get; private set; }

    public string ApiBaseUrl { get; private set; } = "http://localhost:8000";
    public bool IsReady { get; private set; }

    private const string FallbackApiBaseUrl = "http://localhost:8000";

    private void Awake()
    {
        if (Instance != null && Instance != this)
        {
            Destroy(gameObject);
            return;
        }

        Instance = this;
        DontDestroyOnLoad(gameObject);
        StartCoroutine(LoadConfig());
    }

    /// <summary>
    /// Loads config.json from StreamingAssets using UnityWebRequest.
    /// Falls back to default values if the file is missing or cannot be parsed.
    /// </summary>
    public IEnumerator LoadConfig()
    {
        string configPath = System.IO.Path.Combine(Application.streamingAssetsPath, "config.json");

        using (UnityWebRequest request = UnityWebRequest.Get(configPath))
        {
            yield return request.SendWebRequest();

            if (request.result == UnityWebRequest.Result.Success)
            {
                try
                {
                    JObject config = JObject.Parse(request.downloadHandler.text);
                    ApiBaseUrl = config.Value<string>("apiBaseUrl") ?? FallbackApiBaseUrl;
                    Debug.Log($"[GameConfig] Loaded config. ApiBaseUrl={ApiBaseUrl}");
                }
                catch (System.Exception ex)
                {
                    Debug.LogWarning($"[GameConfig] Failed to parse config.json: {ex.Message}. Using fallback.");
                    ApiBaseUrl = FallbackApiBaseUrl;
                }
            }
            else
            {
                Debug.LogWarning($"[GameConfig] Failed to load config.json: {request.error}. Using fallback.");
                ApiBaseUrl = FallbackApiBaseUrl;
            }
        }

        IsReady = true;
    }
}
