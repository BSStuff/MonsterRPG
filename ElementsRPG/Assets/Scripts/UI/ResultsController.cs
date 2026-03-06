using System.Collections;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.SceneManagement;
using TMPro;

/// <summary>
/// Controller for the Results scene.
/// Displays combat outcome (victory/defeat), rewards earned,
/// and saves game state before returning to Home.
/// </summary>
public class ResultsController : MonoBehaviour
{
    [Header("Results Display")]
    [SerializeField] private TMP_Text outcomeText;
    [SerializeField] private TMP_Text roundsText;
    [SerializeField] private TMP_Text xpText;
    [SerializeField] private TMP_Text goldText;

    [Header("Controls")]
    [SerializeField] private Button continueButton;
    [SerializeField] private TMP_Text statusText;

    private void Start()
    {
        continueButton.onClick.AddListener(OnContinueClicked);
        statusText.gameObject.SetActive(false);
        DisplayResults();
    }

    /// <summary>
    /// Populates the results UI from the last combat result stored in SceneData.
    /// </summary>
    private void DisplayResults()
    {
        CombatFinishResponse result = SceneData.LastCombatResult;

        if (result == null)
        {
            outcomeText.text = "No combat data";
            outcomeText.color = Color.white;
            roundsText.text = "";
            xpText.text = "";
            goldText.text = "";
            return;
        }

        bool playerWon = result.Winner == "player";
        outcomeText.text = playerWon ? "Victory!" : "Defeat";
        outcomeText.color = playerWon ? Color.green : Color.red;
        roundsText.text = $"Rounds: {result.Rounds}";

        if (result.Rewards != null)
        {
            xpText.text = $"XP Earned: {result.Rewards.XpEarned}";
            goldText.text = $"Gold Earned: {result.Rewards.GoldEarned}";
        }
        else
        {
            xpText.text = "XP Earned: 0";
            goldText.text = "Gold Earned: 0";
        }
    }

    /// <summary>
    /// Saves the current game state to the server and returns to Home.
    /// On save failure, continues to Home anyway after a brief delay.
    /// </summary>
    private void OnContinueClicked()
    {
        continueButton.interactable = false;
        statusText.gameObject.SetActive(true);
        statusText.text = "Saving...";

        string rawJson = SceneData.RawSaveData?.ToString();

        if (rawJson == null)
        {
            SceneManager.LoadScene("Home");
            return;
        }

        SaveApi.SaveGame(
            rawJson, SceneData.SaveVersion,
            onSuccess: response =>
            {
                SceneData.SaveVersion = response.Version;
                SceneManager.LoadScene("Home");
            },
            onError: error =>
            {
                statusText.text = $"Save failed: {error}. Continuing anyway...";
                StartCoroutine(DelayedLoadHome());
            }
        );
    }

    private IEnumerator DelayedLoadHome()
    {
        yield return new WaitForSeconds(2f);
        SceneManager.LoadScene("Home");
    }
}
