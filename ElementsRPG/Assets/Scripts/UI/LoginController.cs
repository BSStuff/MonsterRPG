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
    [SerializeField] private TMP_InputField confirmPasswordField;
    [SerializeField] private TMP_InputField usernameField;

    [Header("Buttons")]
    [SerializeField] private Button signInButton;
    [SerializeField] private Button signUpButton;
    [SerializeField] private Button toggleModeButton;

    [Header("Labels")]
    [SerializeField] private TMP_Text errorText;
    [SerializeField] private TMP_Text toggleModeText;

    [Header("Layout Groups")]
    [SerializeField] private GameObject confirmPasswordGroup;
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
        confirmPasswordGroup.SetActive(false);
        usernameGroup.SetActive(false);
        signUpButton.gameObject.SetActive(false);
        UpdateToggleModeText();

        // Fix confirm password and username field layouts to match other fields at runtime
        FixExtraFieldLayout(confirmPasswordField, confirmPasswordGroup);
        FixExtraFieldLayout(usernameField, usernameGroup);
    }

    /// <summary>
    /// Handles Tab key navigation between input fields and Enter key submission.
    /// TMP_InputField does not support tab navigation by default in WebGL,
    /// so we handle it manually here.
    /// </summary>
    private void Update()
    {
        // Tab key: cycle focus between input fields
        // Login mode: email -> password -> (cycle)
        // Register mode: email -> password -> confirmPassword -> username -> (cycle)
        if (Input.GetKeyDown(KeyCode.Tab))
        {
            if (emailField.isFocused)
            {
                passwordField.Select();
                passwordField.ActivateInputField();
            }
            else if (passwordField.isFocused)
            {
                if (isRegisterMode && confirmPasswordGroup.activeSelf)
                {
                    confirmPasswordField.Select();
                    confirmPasswordField.ActivateInputField();
                }
                else
                {
                    emailField.Select();
                    emailField.ActivateInputField();
                }
            }
            else if (confirmPasswordField.isFocused)
            {
                if (isRegisterMode && usernameGroup.activeSelf)
                {
                    usernameField.Select();
                    usernameField.ActivateInputField();
                }
                else
                {
                    emailField.Select();
                    emailField.ActivateInputField();
                }
            }
            else if (usernameField.isFocused)
            {
                emailField.Select();
                emailField.ActivateInputField();
            }
        }

        // Enter key: submit the current form
        if (Input.GetKeyDown(KeyCode.Return) || Input.GetKeyDown(KeyCode.KeypadEnter))
        {
            if (isRegisterMode)
                OnSignUpClicked();
            else
                OnSignInClicked();
        }
    }

    /// <summary>
    /// Ensures an input field and its parent group have LayoutElement
    /// settings that match the email and password fields (preferredHeight=50).
    /// Fixes disproportionate sizing caused by the editor setup script.
    /// </summary>
    private void FixExtraFieldLayout(TMP_InputField field, GameObject group)
    {
        if (field == null || group == null)
            return;

        // Fix the input field itself
        var fieldLayout = field.GetComponent<LayoutElement>();
        if (fieldLayout == null)
            fieldLayout = field.gameObject.AddComponent<LayoutElement>();
        fieldLayout.preferredHeight = 50;
        fieldLayout.minHeight = 50;

        // Fix the parent group container
        var groupLayout = group.GetComponent<LayoutElement>();
        if (groupLayout == null)
            groupLayout = group.AddComponent<LayoutElement>();
        groupLayout.preferredHeight = 50;
        groupLayout.minHeight = 50;
    }

    /// <summary>
    /// Toggles between login and register mode.
    /// Shows/hides the username field and swaps sign-in/sign-up buttons.
    /// </summary>
    private void OnToggleMode()
    {
        isRegisterMode = !isRegisterMode;
        confirmPasswordGroup.SetActive(isRegisterMode);
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
        string confirmPassword = confirmPasswordField.text;
        string username = usernameField.text.Trim();

        if (string.IsNullOrEmpty(email) || string.IsNullOrEmpty(password))
        {
            ShowError("Please enter email and password.");
            return;
        }

        if (password != confirmPassword)
        {
            ShowError("Passwords do not match.");
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
