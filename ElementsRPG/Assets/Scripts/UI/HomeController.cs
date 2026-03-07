using System.Collections;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.SceneManagement;
using Newtonsoft.Json.Linq;
using TMPro;

/// <summary>
/// Controller for the Home scene.
/// Loads the player's save data, displays owned monsters in a scroll list,
/// shows player info and balance, and provides combat and logout actions.
/// </summary>
public class HomeController : MonoBehaviour
{
    [Header("Player Info")]
    [SerializeField] private TMP_Text playerInfoText;
    [SerializeField] private TMP_Text balanceText;
    [SerializeField] private TMP_Text statusText;

    [Header("Monster List")]
    [SerializeField] private Transform monsterListContent;
    [SerializeField] private GameObject monsterListItemPrefab;

    [Header("Buttons")]
    [SerializeField] private Button startCombatButton;
    [SerializeField] private Button logoutButton;

    private void Start()
    {
        startCombatButton.onClick.AddListener(OnStartCombatClicked);
        logoutButton.onClick.AddListener(OnLogoutClicked);
        startCombatButton.interactable = false;
        StartCoroutine(LoadPlayerData());
    }

    /// <summary>
    /// Loads the player's save from the server. On 404 (new player),
    /// automatically creates a fresh save.
    /// </summary>
    private IEnumerator LoadPlayerData()
    {
        // Guest mode: data already populated by LoginController, skip API calls
        if (AuthManager.Instance != null && AuthManager.Instance.IsGuest)
        {
            PopulateUI();
            ConfigureGuestCombatButton();
            yield break;
        }

        statusText.gameObject.SetActive(true);
        statusText.text = "Loading...";

        bool requestComplete = false;

        SaveApi.LoadSave(
            onSuccess: saveData =>
            {
                HandleSaveLoaded(saveData);
                requestComplete = true;
            },
            onError: error =>
            {
                if (error.Contains("404") || error.ToLower().Contains("not found"))
                {
                    CreateNewSave();
                }
                else
                {
                    statusText.text = $"Error: {error}";
                }

                requestComplete = true;
            }
        );

        while (!requestComplete)
        {
            yield return null;
        }
    }

    /// <summary>
    /// Creates a fresh save for a first-time player.
    /// </summary>
    private void CreateNewSave()
    {
        statusText.text = "Creating new save...";

        SaveApi.CreateNewSave(
            onSuccess: saveData =>
            {
                HandleSaveLoaded(saveData);
            },
            onError: error =>
            {
                statusText.text = $"Error creating save: {error}";
            }
        );
    }

    /// <summary>
    /// Processes loaded save data into SceneData and populates the UI.
    /// </summary>
    private void HandleSaveLoaded(JObject saveData)
    {
        SceneData.RawSaveData = saveData;
        SceneData.CurrentPlayer = saveData["player"]?.ToObject<PlayerData>();
        SceneData.CurrentMonsters = saveData["monsters"]?.ToObject<MonsterInstance[]>();
        SceneData.SaveVersion = saveData["version"]?.Value<int>() ?? 1;
        PopulateUI();
    }

    /// <summary>
    /// Fills the UI with player info, balance, and monster list.
    /// </summary>
    private void PopulateUI()
    {
        // Player info header
        if (SceneData.CurrentPlayer != null)
        {
            string username = SceneData.CurrentPlayer.Username ?? "Player";
            int level = SceneData.CurrentPlayer.Level;
            playerInfoText.text = $"{username} - Lv.{level}";
        }
        else
        {
            playerInfoText.text = "Player";
        }

        // Fetch balance from economy endpoint
        EconomyApi.GetBalance(
            onSuccess: balance =>
            {
                balanceText.text = $"Gold: {balance.Gold} | Gems: {balance.Gems}";
            },
            onError: error =>
            {
                // Fallback: try to extract from save data
                int gold = SceneData.RawSaveData?["economy"]?["gold"]?.Value<int>() ?? 0;
                int gems = SceneData.RawSaveData?["economy"]?["gems"]?.Value<int>() ?? 0;
                balanceText.text = $"Gold: {gold} | Gems: {gems}";
            }
        );

        // Clear existing monster list items
        for (int i = monsterListContent.childCount - 1; i >= 0; i--)
        {
            Destroy(monsterListContent.GetChild(i).gameObject);
        }

        // Populate monster list
        if (SceneData.CurrentMonsters != null)
        {
            foreach (MonsterInstance monster in SceneData.CurrentMonsters)
            {
                GameObject itemObj = Instantiate(
                    monsterListItemPrefab, monsterListContent);
                MonsterListItem item = itemObj.GetComponent<MonsterListItem>();

                string name = monster.Species != null
                    ? monster.Species.Name
                    : "Unknown";
                string primaryType = (monster.Species?.Types != null
                    && monster.Species.Types.Length > 0)
                    ? monster.Species.Types[0]
                    : "fire";

                item.Setup(name, monster.Level, primaryType);
            }
        }

        startCombatButton.interactable = true;
        statusText.gameObject.SetActive(false);
    }

    /// <summary>
    /// In guest mode, replaces the combat button with a prompt to sign in.
    /// Combat requires server authentication, so guests cannot battle.
    /// </summary>
    private void ConfigureGuestCombatButton()
    {
        startCombatButton.GetComponentInChildren<TMP_Text>().text = "Sign in to Battle!";
        startCombatButton.onClick.RemoveAllListeners();
        startCombatButton.onClick.AddListener(() =>
        {
            AuthManager.Instance.Logout();
            SceneData.Clear();
            SceneManager.LoadScene("Login");
        });
    }

    private void OnStartCombatClicked()
    {
        SceneManager.LoadScene("Combat");
    }

    private void OnLogoutClicked()
    {
        AuthManager.Instance.Logout();
        SceneData.Clear();
        SceneManager.LoadScene("Login");
    }
}
