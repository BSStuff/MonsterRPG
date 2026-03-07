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
    /// Populates SceneData with mock local data for guest mode.
    /// Gives the guest 3 starter monsters so the Home scene can display them.
    /// </summary>
    public static void CreateGuestData()
    {
        CurrentPlayer = new PlayerData
        {
            PlayerId = "guest",
            Username = "Guest",
            Level = 1,
            Experience = 0,
            ActiveAreaId = "area_verdant_meadows"
        };

        CurrentMonsters = new MonsterInstance[]
        {
            new MonsterInstance
            {
                MonsterId = "guest_mon_1",
                Species = new MonsterSpecies
                {
                    SpeciesId = "species_leaflet",
                    Name = "Leaflet",
                    Types = new[] { "grass" },
                    Rarity = "common"
                },
                Level = 5,
                CurrentHp = 45,
                IsFainted = false
            },
            new MonsterInstance
            {
                MonsterId = "guest_mon_2",
                Species = new MonsterSpecies
                {
                    SpeciesId = "species_ember_pup",
                    Name = "Ember Pup",
                    Types = new[] { "fire" },
                    Rarity = "common"
                },
                Level = 5,
                CurrentHp = 50,
                IsFainted = false
            },
            new MonsterInstance
            {
                MonsterId = "guest_mon_3",
                Species = new MonsterSpecies
                {
                    SpeciesId = "species_dewdrop_slime",
                    Name = "Dewdrop Slime",
                    Types = new[] { "water" },
                    Rarity = "common"
                },
                Level = 5,
                CurrentHp = 40,
                IsFainted = false
            }
        };

        SaveVersion = 0;
        RawSaveData = null;
    }

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
