using System.Collections;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.SceneManagement;
using TMPro;

/// <summary>
/// Controller for the Login scene.
/// Handles email/password sign-in and registration with toggle between modes.
/// Auto-skips to Home if already authenticated.
/// </summary>
public class LoginController : MonoBehaviour
{
    [Header("Input Fields")]
    [SerializeField] private TMP_InputField emailField;
    [SerializeField] private TMP_InputField passwordField;
    [SerializeField] private TMP_InputField usernameField;

    [Header("Buttons")]
    [SerializeField] private Button signInButton;
    [SerializeField] private Button signUpButton;
    [SerializeField] private Button toggleModeButton;

    [Header("Labels")]
    [SerializeField] private TMP_Text errorText;
    [SerializeField] private TMP_Text toggleModeText;

    [Header("Layout Groups")]
    [SerializeField] private GameObject usernameGroup;

    private bool isRegisterMode = false;
    private Coroutine hideErrorCoroutine;

    private void Start()
    {
        StartCoroutine(Initialize());
    }

    /// <summary>
    /// Waits for GameConfig to be ready, then checks for existing session
    /// and wires up UI buttons.
    /// </summary>
    private IEnumerator Initialize()
    {
        // Wait for GameConfig to finish loading config.json
        while (GameConfig.Instance == null || !GameConfig.Instance.IsReady)
        {
            yield return null;
        }

        // Auto-skip to Home if already logged in
        if (AuthManager.Instance != null && AuthManager.Instance.IsLoggedIn)
        {
            SceneManager.LoadScene("Home");
            yield break;
        }

        // Wire up button listeners
        signInButton.onClick.AddListener(OnSignInClicked);
        signUpButton.onClick.AddListener(OnSignUpClicked);
        toggleModeButton.onClick.AddListener(OnToggleMode);

        // Initial UI state: login mode
        errorText.gameObject.SetActive(false);
        usernameGroup.SetActive(false);
        signUpButton.gameObject.SetActive(false);
        UpdateToggleModeText();
    }

    /// <summary>
    /// Toggles between login and register mode.
    /// Shows/hides the username field and swaps sign-in/sign-up buttons.
    /// </summary>
    private void OnToggleMode()
    {
        isRegisterMode = !isRegisterMode;
        usernameGroup.SetActive(isRegisterMode);
        signInButton.gameObject.SetActive(!isRegisterMode);
        signUpButton.gameObject.SetActive(isRegisterMode);
        UpdateToggleModeText();
    }

    private void UpdateToggleModeText()
    {
        toggleModeText.text = isRegisterMode
            ? "Already have an account?"
            : "Need an account?";
    }

    /// <summary>
    /// Handles the Sign In button click.
    /// Validates input, disables buttons, and calls the auth API.
    /// </summary>
    private void OnSignInClicked()
    {
        string email = emailField.text.Trim();
        string password = passwordField.text;

        if (string.IsNullOrEmpty(email) || string.IsNullOrEmpty(password))
        {
            ShowError("Please enter email and password.");
            return;
        }

        SetButtonsInteractable(false);

        AuthManager.Instance.Login(email, password,
            onSuccess: response =>
            {
                SceneManager.LoadScene("Home");
            },
            onError: error =>
            {
                ShowError(error);
                SetButtonsInteractable(true);
            }
        );
    }

    /// <summary>
    /// Handles the Sign Up button click.
    /// Validates input including username, disables buttons, and calls the auth API.
    /// </summary>
    private void OnSignUpClicked()
    {
        string email = emailField.text.Trim();
        string password = passwordField.text;
        string username = usernameField.text.Trim();

        if (string.IsNullOrEmpty(email) || string.IsNullOrEmpty(password))
        {
            ShowError("Please enter email and password.");
            return;
        }

        if (string.IsNullOrEmpty(username))
        {
            ShowError("Please enter a username.");
            return;
        }

        SetButtonsInteractable(false);

        AuthManager.Instance.Register(email, password, username,
            onSuccess: response =>
            {
                SceneManager.LoadScene("Home");
            },
            onError: error =>
            {
                ShowError(error);
                SetButtonsInteractable(true);
            }
        );
    }

    /// <summary>
    /// Displays an error message that auto-hides after 5 seconds.
    /// </summary>
    private void ShowError(string message)
    {
        errorText.text = message;
        errorText.gameObject.SetActive(true);

        if (hideErrorCoroutine != null)
        {
            StopCoroutine(hideErrorCoroutine);
        }

        hideErrorCoroutine = StartCoroutine(HideErrorAfterDelay(5f));
    }

    private IEnumerator HideErrorAfterDelay(float seconds)
    {
        yield return new WaitForSeconds(seconds);
        errorText.gameObject.SetActive(false);
        hideErrorCoroutine = null;
    }

    private void SetButtonsInteractable(bool interactable)
    {
        signInButton.interactable = interactable;
        signUpButton.interactable = interactable;
        toggleModeButton.interactable = interactable;
    }
}
