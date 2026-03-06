using System.Collections;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.SceneManagement;
using TMPro;

/// <summary>
/// Controller for the Combat scene.
/// Manages the full combat flow: start session, advance rounds, display HP bars
/// and combat log, finish combat and transition to Results.
/// </summary>
public class CombatController : MonoBehaviour
{
    [Header("Player Monster Panel")]
    [SerializeField] private TMP_Text playerMonsterName;
    [SerializeField] private Slider playerHpBar;
    [SerializeField] private TMP_Text playerHpText;

    [Header("Enemy Monster Panel")]
    [SerializeField] private TMP_Text enemyMonsterName;
    [SerializeField] private Slider enemyHpBar;
    [SerializeField] private TMP_Text enemyHpText;

    [Header("Combat Log")]
    [SerializeField] private TMP_Text combatLogText;
    [SerializeField] private ScrollRect combatLogScroll;

    [Header("Controls")]
    [SerializeField] private Button nextRoundButton;
    [SerializeField] private TMP_Text statusText;
    [SerializeField] private Button backToHomeButton;

    private string sessionId;
    private bool combatFinished;

    private void Start()
    {
        nextRoundButton.onClick.AddListener(OnNextRoundClicked);
        backToHomeButton.onClick.AddListener(OnBackToHomeClicked);
        backToHomeButton.gameObject.SetActive(false);
        nextRoundButton.interactable = false;
        combatLogText.text = "";
        StartCoroutine(StartCombatFlow());
    }

    /// <summary>
    /// Initiates a combat session against a default enemy.
    /// Uses species_leaflet at level 1 as the PoC enemy.
    /// </summary>
    private IEnumerator StartCombatFlow()
    {
        statusText.gameObject.SetActive(true);
        statusText.text = "Starting combat...";

        bool requestComplete = false;

        CombatApi.StartCombat(
            new[] { "species_leaflet" }, 1,
            onSuccess: response =>
            {
                sessionId = response.SessionId;
                UpdateMonsterPanels(response.State);
                AppendLog("Combat started!");
                nextRoundButton.interactable = true;
                statusText.gameObject.SetActive(false);
                requestComplete = true;
            },
            onError: error =>
            {
                statusText.text = $"Error: {error}";
                backToHomeButton.gameObject.SetActive(true);
                requestComplete = true;
            }
        );

        while (!requestComplete)
        {
            yield return null;
        }
    }

    /// <summary>
    /// Advances the combat by one round when the player clicks Next Round.
    /// </summary>
    private void OnNextRoundClicked()
    {
        if (combatFinished)
        {
            return;
        }

        nextRoundButton.interactable = false;

        CombatApi.ExecuteRound(sessionId, OnRoundComplete, OnRoundError);
    }

    private void OnRoundComplete(CombatRoundResponse response)
    {
        UpdateMonsterPanels(response.State);
        AppendCombatLog(response.Actions);

        if (response.State.IsFinished)
        {
            combatFinished = true;
            AppendLog("Combat finished!");
            CombatApi.FinishCombat(sessionId, OnCombatFinished, OnRoundError);
        }
        else
        {
            nextRoundButton.interactable = true;
        }
    }

    private void OnCombatFinished(CombatFinishResponse result)
    {
        SceneData.LastCombatResult = result;
        AppendLog($"Winner: {result.Winner}");
        StartCoroutine(TransitionToResults());
    }

    private IEnumerator TransitionToResults()
    {
        yield return new WaitForSeconds(2f);
        SceneManager.LoadScene("Results");
    }

    /// <summary>
    /// Updates the player and enemy HP bars and name labels from combat state.
    /// </summary>
    private void UpdateMonsterPanels(CombatState state)
    {
        if (state.PlayerMonsters != null && state.PlayerMonsters.Length > 0)
        {
            CombatMonster pm = state.PlayerMonsters[0];
            playerMonsterName.text = pm.Name;
            playerHpBar.maxValue = pm.MaxHp;
            playerHpBar.value = pm.CurrentHp;
            playerHpText.text = $"HP: {pm.CurrentHp}/{pm.MaxHp}";
        }

        if (state.EnemyMonsters != null && state.EnemyMonsters.Length > 0)
        {
            CombatMonster em = state.EnemyMonsters[0];
            enemyMonsterName.text = em.Name;
            enemyHpBar.maxValue = em.MaxHp;
            enemyHpBar.value = em.CurrentHp;
            enemyHpText.text = $"HP: {em.CurrentHp}/{em.MaxHp}";
        }
    }

    /// <summary>
    /// Appends combat action descriptions to the log.
    /// </summary>
    private void AppendCombatLog(CombatAction[] actions)
    {
        if (actions == null)
        {
            return;
        }

        foreach (CombatAction action in actions)
        {
            string msg = $"{action.Attacker} used {action.Skill} on " +
                         $"{action.Target} for {action.Damage} damage!";

            if (action.IsCritical)
            {
                msg += " Critical hit!";
            }

            if (!string.IsNullOrEmpty(action.Effectiveness)
                && action.Effectiveness != "normal")
            {
                msg += $" ({action.Effectiveness})";
            }

            AppendLog(msg);
        }
    }

    /// <summary>
    /// Appends a message to the combat log and scrolls to the bottom.
    /// </summary>
    private void AppendLog(string msg)
    {
        combatLogText.text += msg + "\n";
        Canvas.ForceUpdateCanvases();
        combatLogScroll.verticalNormalizedPosition = 0f;
    }

    private void OnRoundError(string error)
    {
        if (error.Contains("404"))
        {
            AppendLog("Combat session expired.");
            backToHomeButton.gameObject.SetActive(true);
        }
        else
        {
            AppendLog($"Error: {error}");
            nextRoundButton.interactable = true;
        }
    }

    private void OnBackToHomeClicked()
    {
        SceneManager.LoadScene("Home");
    }
}
