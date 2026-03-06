using System;
using Newtonsoft.Json;

// ──────────────────────────────────────────────
// Response Envelope
// ──────────────────────────────────────────────

[Serializable]
public class ApiResponse<T>
{
    [JsonProperty("success")]
    public bool Success;

    [JsonProperty("data")]
    public T Data;

    [JsonProperty("timestamp")]
    public string Timestamp;
}

[Serializable]
public class ApiError
{
    [JsonProperty("error")]
    public ErrorDetail Error;
}

[Serializable]
public class ErrorDetail
{
    [JsonProperty("code")]
    public string Code;

    [JsonProperty("message")]
    public string Message;

    [JsonProperty("timestamp")]
    public string Timestamp;
}

// ──────────────────────────────────────────────
// Auth
// ──────────────────────────────────────────────

[Serializable]
public class AuthRequest
{
    [JsonProperty("email")]
    public string Email;

    [JsonProperty("password")]
    public string Password;
}

[Serializable]
public class RegisterRequest
{
    [JsonProperty("email")]
    public string Email;

    [JsonProperty("password")]
    public string Password;

    [JsonProperty("username")]
    public string Username;
}

[Serializable]
public class RefreshRequest
{
    [JsonProperty("refresh_token")]
    public string RefreshToken;
}

[Serializable]
public class AuthResponse
{
    [JsonProperty("access_token")]
    public string AccessToken;

    [JsonProperty("refresh_token")]
    public string RefreshToken;

    [JsonProperty("token_type")]
    public string TokenType;

    [JsonProperty("expires_in")]
    public int ExpiresIn;

    [JsonProperty("user")]
    public AuthUser User;
}

[Serializable]
public class AuthUser
{
    [JsonProperty("id")]
    public string Id;

    [JsonProperty("email")]
    public string Email;

    [JsonProperty("username")]
    public string Username;
}

// ──────────────────────────────────────────────
// Monster Species (bestiary)
// ──────────────────────────────────────────────

[Serializable]
public class StatBlock
{
    [JsonProperty("hp")]
    public int Hp;

    [JsonProperty("attack")]
    public int Attack;

    [JsonProperty("defense")]
    public int Defense;

    [JsonProperty("speed")]
    public int Speed;

    [JsonProperty("magic_attack")]
    public int MagicAttack;

    [JsonProperty("magic_defense")]
    public int MagicDefense;
}

[Serializable]
public class MonsterSpecies
{
    [JsonProperty("species_id")]
    public string SpeciesId;

    [JsonProperty("name")]
    public string Name;

    [JsonProperty("types")]
    public string[] Types;

    [JsonProperty("rarity")]
    public string Rarity;

    [JsonProperty("base_stats")]
    public StatBlock BaseStats;

    [JsonProperty("passive_trait")]
    public string PassiveTrait;

    [JsonProperty("passive_description")]
    public string PassiveDescription;

    [JsonProperty("learnable_skill_ids")]
    public string[] LearnableSkillIds;
}

// ──────────────────────────────────────────────
// Monster Instance (owned)
// ──────────────────────────────────────────────

[Serializable]
public class MonsterInstance
{
    [JsonProperty("monster_id")]
    public string MonsterId;

    [JsonProperty("species")]
    public MonsterSpecies Species;

    [JsonProperty("level")]
    public int Level;

    [JsonProperty("experience")]
    public int Experience;

    [JsonProperty("bond_level")]
    public int BondLevel;

    [JsonProperty("equipped_skill_ids")]
    public string[] EquippedSkillIds;

    [JsonProperty("current_hp")]
    public int CurrentHp;

    [JsonProperty("is_fainted")]
    public bool IsFainted;
}

// ──────────────────────────────────────────────
// Player
// ──────────────────────────────────────────────

[Serializable]
public class PlayerData
{
    [JsonProperty("player_id")]
    public string PlayerId;

    [JsonProperty("username")]
    public string Username;

    [JsonProperty("level")]
    public int Level;

    [JsonProperty("experience")]
    public int Experience;

    [JsonProperty("team_monster_ids")]
    public string[] TeamMonsterIds;

    [JsonProperty("owned_monster_ids")]
    public string[] OwnedMonsterIds;

    [JsonProperty("active_area_id")]
    public string ActiveAreaId;

    [JsonProperty("action_queue_slots")]
    public int ActionQueueSlots;
}

// ──────────────────────────────────────────────
// Combat
// ──────────────────────────────────────────────

[Serializable]
public class CombatStartRequest
{
    [JsonProperty("enemy_species_ids")]
    public string[] EnemySpeciesIds;

    [JsonProperty("enemy_level")]
    public int EnemyLevel;
}

[Serializable]
public class CombatStartResponse
{
    [JsonProperty("session_id")]
    public string SessionId;

    [JsonProperty("state")]
    public CombatState State;
}

[Serializable]
public class CombatState
{
    [JsonProperty("round")]
    public int Round;

    [JsonProperty("is_finished")]
    public bool IsFinished;

    [JsonProperty("player_monsters")]
    public CombatMonster[] PlayerMonsters;

    [JsonProperty("enemy_monsters")]
    public CombatMonster[] EnemyMonsters;
}

[Serializable]
public class CombatMonster
{
    [JsonProperty("monster_id")]
    public string MonsterId;

    [JsonProperty("name")]
    public string Name;

    [JsonProperty("species_id")]
    public string SpeciesId;

    [JsonProperty("level")]
    public int Level;

    [JsonProperty("current_hp")]
    public int CurrentHp;

    [JsonProperty("max_hp")]
    public int MaxHp;

    [JsonProperty("is_fainted")]
    public bool IsFainted;

    [JsonProperty("types")]
    public string[] Types;
}

[Serializable]
public class CombatAction
{
    [JsonProperty("attacker")]
    public string Attacker;

    [JsonProperty("target")]
    public string Target;

    [JsonProperty("skill")]
    public string Skill;

    [JsonProperty("damage")]
    public int Damage;

    [JsonProperty("is_critical")]
    public bool IsCritical;

    [JsonProperty("effectiveness")]
    public string Effectiveness;
}

[Serializable]
public class CombatRoundResponse
{
    [JsonProperty("state")]
    public CombatState State;

    [JsonProperty("actions")]
    public CombatAction[] Actions;
}

[Serializable]
public class CombatFinishResponse
{
    [JsonProperty("finished")]
    public bool Finished;

    [JsonProperty("rounds")]
    public int Rounds;

    [JsonProperty("winner")]
    public string Winner;

    [JsonProperty("rewards")]
    public CombatRewards Rewards;
}

[Serializable]
public class CombatRewards
{
    [JsonProperty("gold_earned")]
    public int GoldEarned;

    [JsonProperty("xp_earned")]
    public int XpEarned;
}

// ──────────────────────────────────────────────
// Economy
// ──────────────────────────────────────────────

[Serializable]
public class BalanceResponse
{
    [JsonProperty("gold")]
    public int Gold;

    [JsonProperty("gems")]
    public int Gems;
}

// ──────────────────────────────────────────────
// Save/Load
// ──────────────────────────────────────────────

[Serializable]
public class SaveRequest
{
    [JsonProperty("save_data")]
    public object SaveData;

    [JsonProperty("expected_version")]
    public int? ExpectedVersion;
}

[Serializable]
public class SaveResponse
{
    [JsonProperty("success")]
    public bool Success;

    [JsonProperty("version")]
    public int Version;

    [JsonProperty("timestamp")]
    public string Timestamp;
}
