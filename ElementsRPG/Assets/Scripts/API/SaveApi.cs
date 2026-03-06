using System;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

/// <summary>
/// Static API wrapper for save/load endpoints.
/// Uses ApiClient.Instance for all HTTP requests.
/// Save data is passed as raw JObject to support the passthrough strategy --
/// the client preserves all fields it does not understand.
/// </summary>
public static class SaveApi
{
    /// <summary>
    /// Loads the player's existing save from the server.
    /// Returns a JObject preserving all fields for passthrough.
    /// </summary>
    public static void LoadSave(Action<JObject> onSuccess, Action<string> onError)
    {
        ApiClient.Instance.StartRequest(
            ApiClient.Instance.Get<JObject>("/saves/", onSuccess, onError)
        );
    }

    /// <summary>
    /// Creates a new save for a first-time player.
    /// Returns 409 if a save already exists.
    /// </summary>
    public static void CreateNewSave(Action<JObject> onSuccess, Action<string> onError)
    {
        ApiClient.Instance.StartRequest(
            ApiClient.Instance.PostNoBody<JObject>("/saves/new", onSuccess, onError)
        );
    }

    /// <summary>
    /// Persists the current game state to the server.
    /// Uses optimistic locking -- pass expectedVersion from the last load/save
    /// to detect concurrent modifications (server returns 409 on mismatch).
    /// </summary>
    /// <param name="rawSaveJson">
    /// The full GameSaveData as a JSON string (typically stored in SceneData.RawSaveJson).
    /// </param>
    /// <param name="expectedVersion">
    /// The version number from the last load or save, or null to skip version checking.
    /// </param>
    public static void SaveGame(
        string rawSaveJson, int? expectedVersion,
        Action<SaveResponse> onSuccess, Action<string> onError)
    {
        JObject saveData;
        try
        {
            saveData = JObject.Parse(rawSaveJson);
        }
        catch (JsonReaderException ex)
        {
            onError?.Invoke("Invalid save data JSON: " + ex.Message);
            return;
        }

        var body = new
        {
            save_data = saveData,
            expected_version = expectedVersion
        };

        ApiClient.Instance.StartRequest(
            ApiClient.Instance.PostRaw<SaveResponse>("/saves/", body, onSuccess, onError)
        );
    }
}
