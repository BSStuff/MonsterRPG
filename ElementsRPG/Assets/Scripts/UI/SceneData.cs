using Newtonsoft.Json.Linq;

/// <summary>
/// Static class for passing data between scenes.
/// Holds the raw save JSON (for passthrough), extracted typed objects,
/// the save version for optimistic locking, and the last combat result.
/// </summary>
public static class SceneData
{
    /// <summary>Full save JSON blob for round-trip passthrough to the server.</summary>
    public static JObject RawSaveData;

    /// <summary>Extracted player info from the save data.</summary>
    public static PlayerData CurrentPlayer;

    /// <summary>Extracted monster instances from the save data.</summary>
    public static MonsterInstance[] CurrentMonsters;

    /// <summary>Save version for optimistic locking (incremented server-side).</summary>
    public static int SaveVersion;

    /// <summary>Result of the last completed combat session.</summary>
    public static CombatFinishResponse LastCombatResult;

    /// <summary>
    /// Resets all cross-scene state to defaults.
    /// Call on logout or when starting a fresh session.
    /// </summary>
    public static void Clear()
    {
        RawSaveData = null;
        CurrentPlayer = null;
        CurrentMonsters = null;
        SaveVersion = 0;
        LastCombatResult = null;
    }
}
