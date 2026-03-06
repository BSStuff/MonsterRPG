using System;

/// <summary>
/// Static API wrapper for monster endpoints.
/// Uses ApiClient.Instance for all HTTP requests.
/// </summary>
public static class MonsterApi
{
    /// <summary>
    /// Fetches the full bestiary (all monster species definitions).
    /// This is a public endpoint -- no authentication required.
    /// </summary>
    public static void GetBestiary(
        Action<MonsterSpecies[]> onSuccess, Action<string> onError)
    {
        ApiClient.Instance.StartRequest(
            ApiClient.Instance.Get<MonsterSpecies[]>(
                "/monsters/bestiary", onSuccess, onError)
        );
    }

    /// <summary>
    /// Fetches all monsters owned by the authenticated player.
    /// Requires authentication.
    /// </summary>
    public static void GetOwnedMonsters(
        Action<MonsterInstance[]> onSuccess, Action<string> onError)
    {
        ApiClient.Instance.StartRequest(
            ApiClient.Instance.Get<MonsterInstance[]>(
                "/monsters/owned", onSuccess, onError)
        );
    }
}
