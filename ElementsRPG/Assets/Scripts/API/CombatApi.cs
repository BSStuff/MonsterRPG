using System;

/// <summary>
/// Static API wrapper for combat endpoints.
/// Uses ApiClient.Instance for all HTTP requests.
/// </summary>
public static class CombatApi
{
    /// <summary>
    /// Starts a new combat session against the specified enemy species at the given level.
    /// The server creates a combat session and returns the initial state with session ID.
    /// </summary>
    /// <param name="enemySpeciesIds">Array of species IDs for the enemy team (1-6).</param>
    /// <param name="enemyLevel">Enemy level (1-100).</param>
    public static void StartCombat(
        string[] enemySpeciesIds, int enemyLevel,
        Action<CombatStartResponse> onSuccess, Action<string> onError)
    {
        var body = new CombatStartRequest
        {
            EnemySpeciesIds = enemySpeciesIds,
            EnemyLevel = enemyLevel
        };

        ApiClient.Instance.StartRequest(
            ApiClient.Instance.Post<CombatStartResponse>(
                "/combat/start", body, onSuccess, onError)
        );
    }

    /// <summary>
    /// Executes one round of combat. The server resolves all actions (attacks, abilities)
    /// and returns the updated state plus a list of actions that occurred.
    /// </summary>
    /// <param name="sessionId">The combat session ID from StartCombat.</param>
    public static void ExecuteRound(
        string sessionId,
        Action<CombatRoundResponse> onSuccess, Action<string> onError)
    {
        ApiClient.Instance.StartRequest(
            ApiClient.Instance.PostNoBody<CombatRoundResponse>(
                "/combat/" + sessionId + "/round", onSuccess, onError)
        );
    }

    /// <summary>
    /// Finishes the combat session and collects rewards (XP, gold).
    /// Rewards are applied server-side to the player's save data.
    /// </summary>
    /// <param name="sessionId">The combat session ID from StartCombat.</param>
    public static void FinishCombat(
        string sessionId,
        Action<CombatFinishResponse> onSuccess, Action<string> onError)
    {
        ApiClient.Instance.StartRequest(
            ApiClient.Instance.PostNoBody<CombatFinishResponse>(
                "/combat/" + sessionId + "/finish", onSuccess, onError)
        );
    }
}
