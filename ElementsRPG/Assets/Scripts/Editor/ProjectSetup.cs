using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.SceneManagement;
using UnityEngine.EventSystems;
using TMPro;
using System.IO;
using System.Reflection;

/// <summary>
/// Editor-only script that creates all 4 scenes, the MonsterListItem prefab,
/// singleton GameObjects, and configures Build Settings for the ElementsRPG PoC.
/// Run via the menu: ElementsRPG > Setup Project.
/// </summary>
public static class ProjectSetup
{
    private const string ScenesFolder = "Assets/Scenes";
    private const string PrefabsFolder = "Assets/Prefabs";
    private const string PrefabPath = "Assets/Prefabs/MonsterListItem.prefab";

    // ----------------------------------------------------------------
    // Menu Entry Point
    // ----------------------------------------------------------------

    [MenuItem("ElementsRPG/Setup Project")]
    public static void SetupProject()
    {
        CreateFolders();
        CheckTMPEssentials();
        CreateMonsterListItemPrefab();
        CreateLoginScene();
        CreateHomeScene();
        CreateCombatScene();
        CreateResultsScene();
        ConfigureBuildSettings();

        // Open the Login scene so the user starts there
        EditorSceneManager.OpenScene($"{ScenesFolder}/Login.unity");

        Debug.Log("[ElementsRPG] Project setup complete! All 4 scenes, prefab, " +
                  "singletons, and build settings are configured.");
    }

    // ----------------------------------------------------------------
    // Step 1: Folders
    // ----------------------------------------------------------------

    private static void CreateFolders()
    {
        if (!AssetDatabase.IsValidFolder(ScenesFolder))
        {
            AssetDatabase.CreateFolder("Assets", "Scenes");
        }

        if (!AssetDatabase.IsValidFolder(PrefabsFolder))
        {
            AssetDatabase.CreateFolder("Assets", "Prefabs");
        }
    }

    // ----------------------------------------------------------------
    // Step 2: TMP Essentials Check
    // ----------------------------------------------------------------

    private static void CheckTMPEssentials()
    {
        // TMP essential resources live at "Assets/TextMesh Pro" after import
        string tmpFolder = "Assets/TextMesh Pro";
        if (AssetDatabase.IsValidFolder(tmpFolder))
        {
            return;
        }

        // Try to auto-import via reflection (the method may not exist in all versions)
        var tmpPackageType = System.Type.GetType(
            "TMPro.TMP_PackageUtilities, Unity.TextMeshPro.Editor");
        if (tmpPackageType != null)
        {
            var importMethod = tmpPackageType.GetMethod(
                "ImportProjectResourcesMenu",
                BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic);
            if (importMethod != null)
            {
                importMethod.Invoke(null, null);
                Debug.Log("[ElementsRPG] TMP Essentials imported automatically.");
                return;
            }
        }

        Debug.LogWarning(
            "[ElementsRPG] TextMesh Pro essential resources not found. " +
            "Please import them manually: Window > TextMeshPro > Import TMP Essential Resources. " +
            "Then re-run ElementsRPG > Setup Project.");
    }

    // ----------------------------------------------------------------
    // Step 3: MonsterListItem Prefab
    // ----------------------------------------------------------------

    private static void CreateMonsterListItemPrefab()
    {
        // Root
        var root = new GameObject("MonsterListItem");
        var rootRT = root.AddComponent<RectTransform>();
        rootRT.sizeDelta = new Vector2(500, 80);

        var hlg = root.AddComponent<HorizontalLayoutGroup>();
        hlg.spacing = 10;
        hlg.childAlignment = TextAnchor.MiddleLeft;
        hlg.childForceExpandWidth = false;
        hlg.childForceExpandHeight = false;
        hlg.childControlWidth = false;
        hlg.childControlHeight = false;

        var rootLE = root.AddComponent<LayoutElement>();
        rootLE.preferredHeight = 80;
        rootLE.minHeight = 80;

        // ElementIcon
        var iconGO = new GameObject("ElementIcon");
        iconGO.transform.SetParent(root.transform, false);
        var iconRT = iconGO.AddComponent<RectTransform>();
        iconRT.sizeDelta = new Vector2(50, 50);
        var iconImg = iconGO.AddComponent<Image>();
        iconImg.color = Color.white;
        var iconLE = iconGO.AddComponent<LayoutElement>();
        iconLE.preferredWidth = 50;
        iconLE.preferredHeight = 50;
        iconLE.minWidth = 50;
        iconLE.minHeight = 50;

        // NameText
        var nameGO = CreateTMPObject(root.transform, "NameText", "Monster", 24,
            TextAlignmentOptions.MidlineLeft, Color.white, FontStyles.Bold);
        var nameLE = nameGO.AddComponent<LayoutElement>();
        nameLE.preferredWidth = 200;

        // LevelText
        var levelGO = CreateTMPObject(root.transform, "LevelText", "Lv.1", 18,
            TextAlignmentOptions.MidlineLeft, Color.white, FontStyles.Normal);
        var levelLE = levelGO.AddComponent<LayoutElement>();
        levelLE.preferredWidth = 80;

        // TypeText
        var typeGO = CreateTMPObject(root.transform, "TypeText", "Fire", 16,
            TextAlignmentOptions.MidlineLeft, Color.white, FontStyles.Normal);
        var typeLE = typeGO.AddComponent<LayoutElement>();
        typeLE.preferredWidth = 100;

        // Add MonsterListItem component and wire fields
        var listItem = root.AddComponent<MonsterListItem>();
        SetPrivateField(listItem, "elementIcon", iconImg);
        SetPrivateField(listItem, "nameText", nameGO.GetComponent<TextMeshProUGUI>());
        SetPrivateField(listItem, "levelText", levelGO.GetComponent<TextMeshProUGUI>());
        SetPrivateField(listItem, "typeText", typeGO.GetComponent<TextMeshProUGUI>());

        // Save prefab
        PrefabUtility.SaveAsPrefabAsset(root, PrefabPath);
        Object.DestroyImmediate(root);
        Debug.Log("[ElementsRPG] Created MonsterListItem prefab.");
    }

    // ----------------------------------------------------------------
    // Step 4: Login Scene
    // ----------------------------------------------------------------

    private static void CreateLoginScene()
    {
        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

        // Singletons (persist via DontDestroyOnLoad)
        CreateSingleton<GameConfig>("GameConfig");
        CreateSingleton<ApiClient>("ApiClient");
        CreateSingleton<AuthManager>("AuthManager");

        // EventSystem
        CreateEventSystem();

        // Canvas
        var canvas = CreateCanvas("Canvas");
        var canvasTransform = canvas.transform;

        // LoginPanel
        var loginPanel = CreateUIObject("LoginPanel", canvasTransform);
        var panelRT = loginPanel.GetComponent<RectTransform>();
        panelRT.anchorMin = new Vector2(0.5f, 0.5f);
        panelRT.anchorMax = new Vector2(0.5f, 0.5f);
        panelRT.pivot = new Vector2(0.5f, 0.5f);
        panelRT.sizeDelta = new Vector2(400, 575);
        panelRT.anchoredPosition = Vector2.zero;

        var panelImg = loginPanel.AddComponent<Image>();
        panelImg.color = new Color(0.15f, 0.15f, 0.2f, 1f);

        var vlg = loginPanel.AddComponent<VerticalLayoutGroup>();
        vlg.spacing = 15;
        vlg.padding = new RectOffset(30, 30, 30, 30);
        vlg.childAlignment = TextAnchor.UpperCenter;
        vlg.childForceExpandWidth = true;
        vlg.childForceExpandHeight = false;
        vlg.childControlWidth = true;
        vlg.childControlHeight = false;

        // TitleText
        var titleGO = CreateTMPObject(loginPanel.transform, "TitleText", "ElementsRPG", 36,
            TextAlignmentOptions.Center, Color.white, FontStyles.Bold);
        var titleLE = titleGO.AddComponent<LayoutElement>();
        titleLE.preferredHeight = 50;

        // EmailField
        var emailField = CreateTMPInputField(loginPanel.transform, "EmailField", "Email", 50);

        // PasswordField
        var passwordField = CreateTMPInputField(
            loginPanel.transform, "PasswordField", "Password", 50);
        passwordField.GetComponent<TMP_InputField>().contentType =
            TMP_InputField.ContentType.Password;

        // ConfirmPasswordGroup (starts inactive — only shown in register mode)
        // No VerticalLayoutGroup — just a container with fixed height so the child field fits exactly
        var confirmPasswordGroup = CreateUIObject("ConfirmPasswordGroup", loginPanel.transform);
        var cpgLE = confirmPasswordGroup.AddComponent<LayoutElement>();
        cpgLE.preferredHeight = 50;
        cpgLE.minHeight = 50;
        // Stretch the child field to fill the group
        var confirmPasswordField = CreateTMPInputField(
            confirmPasswordGroup.transform, "ConfirmPasswordField", "Confirm Password", 50);
        var cpfRT = confirmPasswordField.GetComponent<RectTransform>();
        cpfRT.anchorMin = Vector2.zero;
        cpfRT.anchorMax = Vector2.one;
        cpfRT.offsetMin = Vector2.zero;
        cpfRT.offsetMax = Vector2.zero;
        confirmPasswordField.GetComponent<TMP_InputField>().contentType =
            TMP_InputField.ContentType.Password;
        confirmPasswordGroup.SetActive(false);

        // UsernameGroup (same pattern — container with fixed height, no layout group)
        var usernameGroup = CreateUIObject("UsernameGroup", loginPanel.transform);
        var ugLE = usernameGroup.AddComponent<LayoutElement>();
        ugLE.preferredHeight = 50;
        ugLE.minHeight = 50;
        var usernameField = CreateTMPInputField(
            usernameGroup.transform, "UsernameField", "Username", 50);
        var ufRT = usernameField.GetComponent<RectTransform>();
        ufRT.anchorMin = Vector2.zero;
        ufRT.anchorMax = Vector2.one;
        ufRT.offsetMin = Vector2.zero;
        ufRT.offsetMax = Vector2.zero;

        // SignInButton
        var signInBtn = CreateButtonWithText(
            loginPanel.transform, "SignInButton", "Sign In", 45,
            new Color(0.2f, 0.6f, 1f, 1f), new Color(0.3f, 0.7f, 1f, 1f));

        // SignUpButton (starts inactive)
        var signUpBtn = CreateButtonWithText(
            loginPanel.transform, "SignUpButton", "Sign Up", 45,
            new Color(0.2f, 0.6f, 1f, 1f), new Color(0.3f, 0.7f, 1f, 1f));
        signUpBtn.SetActive(false);

        // ToggleModeButton
        var toggleModeBtn = CreateButtonWithText(
            loginPanel.transform, "ToggleModeButton", "Need an account?", 45,
            new Color(0f, 0f, 0f, 0f), new Color(1f, 1f, 1f, 0.1f));
        var toggleText = toggleModeBtn.GetComponentInChildren<TextMeshProUGUI>();
        toggleText.fontSize = 14;

        // GuestButton — neutral grey, smaller height
        var guestBtn = CreateButtonWithText(
            loginPanel.transform, "GuestButton", "Continue as Guest", 40,
            new Color(0.35f, 0.35f, 0.4f, 1f), new Color(0.45f, 0.45f, 0.5f, 1f));
        var guestBtnLE = guestBtn.GetComponent<LayoutElement>();
        if (guestBtnLE == null)
            guestBtnLE = guestBtn.AddComponent<LayoutElement>();
        guestBtnLE.preferredHeight = 40;

        // ErrorText (starts inactive)
        var errorGO = CreateTMPObject(loginPanel.transform, "ErrorText", "", 14,
            TextAlignmentOptions.Center, Color.red, FontStyles.Normal);
        var errorLE = errorGO.AddComponent<LayoutElement>();
        errorLE.preferredHeight = 30;
        errorGO.SetActive(false);

        // LoginController
        var controllerGO = new GameObject("LoginController");
        var loginCtrl = controllerGO.AddComponent<LoginController>();

        SetPrivateField(loginCtrl, "emailField",
            emailField.GetComponent<TMP_InputField>());
        SetPrivateField(loginCtrl, "passwordField",
            passwordField.GetComponent<TMP_InputField>());
        SetPrivateField(loginCtrl, "confirmPasswordField",
            confirmPasswordField.GetComponent<TMP_InputField>());
        SetPrivateField(loginCtrl, "usernameField",
            usernameField.GetComponent<TMP_InputField>());
        SetPrivateField(loginCtrl, "signInButton",
            signInBtn.GetComponent<Button>());
        SetPrivateField(loginCtrl, "signUpButton",
            signUpBtn.GetComponent<Button>());
        SetPrivateField(loginCtrl, "toggleModeButton",
            toggleModeBtn.GetComponent<Button>());
        SetPrivateField(loginCtrl, "guestButton",
            guestBtn.GetComponent<Button>());
        SetPrivateField(loginCtrl, "errorText",
            errorGO.GetComponent<TextMeshProUGUI>());
        SetPrivateField(loginCtrl, "toggleModeText",
            toggleText);
        SetPrivateField(loginCtrl, "confirmPasswordGroup", confirmPasswordGroup);
        SetPrivateField(loginCtrl, "usernameGroup", usernameGroup);

        EditorSceneManager.SaveScene(scene, $"{ScenesFolder}/Login.unity");
        Debug.Log("[ElementsRPG] Created Login scene.");
    }

    // ----------------------------------------------------------------
    // Step 5: Home Scene
    // ----------------------------------------------------------------

    private static void CreateHomeScene()
    {
        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

        CreateEventSystem();
        var canvas = CreateCanvas("Canvas");
        var canvasT = canvas.transform;

        // HeaderPanel (top)
        var header = CreateUIObject("HeaderPanel", canvasT);
        var headerRT = header.GetComponent<RectTransform>();
        SetAnchorStretchTop(headerRT, 100);
        var headerImg = header.AddComponent<Image>();
        headerImg.color = new Color(0.12f, 0.12f, 0.18f, 1f);
        var headerHLG = header.AddComponent<HorizontalLayoutGroup>();
        headerHLG.spacing = 20;
        headerHLG.padding = new RectOffset(20, 20, 10, 10);
        headerHLG.childAlignment = TextAnchor.MiddleLeft;
        headerHLG.childForceExpandWidth = true;
        headerHLG.childForceExpandHeight = false;
        headerHLG.childControlWidth = true;
        headerHLG.childControlHeight = false;

        var playerInfoGO = CreateTMPObject(header.transform, "PlayerInfoText",
            "Player - Lv.1", 24, TextAlignmentOptions.MidlineLeft, Color.white,
            FontStyles.Bold);
        var balanceGO = CreateTMPObject(header.transform, "BalanceText",
            "Gold: 0 | Gems: 0", 20, TextAlignmentOptions.MidlineRight, Color.white,
            FontStyles.Normal);

        // MonsterScrollView (middle)
        var scrollView = CreateUIObject("MonsterScrollView", canvasT);
        var scrollRT = scrollView.GetComponent<RectTransform>();
        scrollRT.anchorMin = new Vector2(0, 0);
        scrollRT.anchorMax = new Vector2(1, 1);
        scrollRT.offsetMin = new Vector2(0, 80);  // leave room for bottom
        scrollRT.offsetMax = new Vector2(0, -100); // leave room for header
        var scrollBg = scrollView.AddComponent<Image>();
        scrollBg.color = new Color(0.1f, 0.1f, 0.15f, 0.5f);
        var scrollRect = scrollView.AddComponent<ScrollRect>();
        scrollRect.horizontal = false;

        var viewport = CreateUIObject("Viewport", scrollView.transform);
        var vpRT = viewport.GetComponent<RectTransform>();
        vpRT.anchorMin = Vector2.zero;
        vpRT.anchorMax = Vector2.one;
        vpRT.offsetMin = Vector2.zero;
        vpRT.offsetMax = Vector2.zero;
        viewport.AddComponent<Image>().color = Color.clear;
        viewport.AddComponent<Mask>().showMaskGraphic = false;

        var content = CreateUIObject("Content", viewport.transform);
        var contentRT = content.GetComponent<RectTransform>();
        contentRT.anchorMin = new Vector2(0, 1);
        contentRT.anchorMax = new Vector2(1, 1);
        contentRT.pivot = new Vector2(0.5f, 1f);
        contentRT.offsetMin = new Vector2(0, 0);
        contentRT.offsetMax = new Vector2(0, 0);
        var contentVLG = content.AddComponent<VerticalLayoutGroup>();
        contentVLG.spacing = 5;
        contentVLG.padding = new RectOffset(10, 10, 10, 10);
        contentVLG.childForceExpandWidth = true;
        contentVLG.childForceExpandHeight = false;
        contentVLG.childControlWidth = true;
        contentVLG.childControlHeight = false;
        var contentCSF = content.AddComponent<ContentSizeFitter>();
        contentCSF.verticalFit = ContentSizeFitter.FitMode.PreferredSize;

        scrollRect.content = contentRT;
        scrollRect.viewport = vpRT;

        // BottomPanel
        var bottom = CreateUIObject("BottomPanel", canvasT);
        var bottomRT = bottom.GetComponent<RectTransform>();
        SetAnchorStretchBottom(bottomRT, 80);
        var bottomImg = bottom.AddComponent<Image>();
        bottomImg.color = new Color(0.12f, 0.12f, 0.18f, 1f);
        var bottomHLG = bottom.AddComponent<HorizontalLayoutGroup>();
        bottomHLG.spacing = 20;
        bottomHLG.padding = new RectOffset(20, 20, 10, 10);
        bottomHLG.childAlignment = TextAnchor.MiddleCenter;
        bottomHLG.childForceExpandWidth = true;
        bottomHLG.childForceExpandHeight = false;
        bottomHLG.childControlWidth = true;
        bottomHLG.childControlHeight = false;

        var startCombatBtn = CreateButtonWithText(
            bottom.transform, "StartCombatButton", "Start Combat", 50,
            new Color(0.13f, 0.77f, 0.37f, 1f), new Color(0.2f, 0.85f, 0.45f, 1f));
        var logoutBtn = CreateButtonWithText(
            bottom.transform, "LogoutButton", "Logout", 50,
            new Color(0.94f, 0.27f, 0.27f, 1f), new Color(1f, 0.35f, 0.35f, 1f));

        // StatusText (center)
        var statusGO = CreateTMPObject(canvasT, "StatusText", "Loading...", 20,
            TextAlignmentOptions.Center, Color.white, FontStyles.Normal);
        var statusRT = statusGO.GetComponent<RectTransform>();
        statusRT.anchorMin = new Vector2(0.5f, 0.5f);
        statusRT.anchorMax = new Vector2(0.5f, 0.5f);
        statusRT.sizeDelta = new Vector2(400, 50);
        statusRT.anchoredPosition = Vector2.zero;

        // HomeController
        var controllerGO = new GameObject("HomeController");
        var homeCtrl = controllerGO.AddComponent<HomeController>();

        // Load the prefab
        var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(PrefabPath);

        SetPrivateField(homeCtrl, "playerInfoText",
            playerInfoGO.GetComponent<TextMeshProUGUI>());
        SetPrivateField(homeCtrl, "balanceText",
            balanceGO.GetComponent<TextMeshProUGUI>());
        SetPrivateField(homeCtrl, "statusText",
            statusGO.GetComponent<TextMeshProUGUI>());
        SetPrivateField(homeCtrl, "monsterListContent", content.transform);
        SetPrivateField(homeCtrl, "monsterListItemPrefab", prefab);
        SetPrivateField(homeCtrl, "startCombatButton",
            startCombatBtn.GetComponent<Button>());
        SetPrivateField(homeCtrl, "logoutButton",
            logoutBtn.GetComponent<Button>());

        EditorSceneManager.SaveScene(scene, $"{ScenesFolder}/Home.unity");
        Debug.Log("[ElementsRPG] Created Home scene.");
    }

    // ----------------------------------------------------------------
    // Step 6: Combat Scene
    // ----------------------------------------------------------------

    private static void CreateCombatScene()
    {
        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

        CreateEventSystem();
        var canvas = CreateCanvas("Canvas");
        var canvasT = canvas.transform;

        // PlayerPanel (left)
        var playerPanel = CreateUIObject("PlayerPanel", canvasT);
        var ppRT = playerPanel.GetComponent<RectTransform>();
        ppRT.anchorMin = new Vector2(0, 0.3f);
        ppRT.anchorMax = new Vector2(0.45f, 0.9f);
        ppRT.offsetMin = new Vector2(20, 0);
        ppRT.offsetMax = new Vector2(-10, -10);
        var ppVLG = playerPanel.AddComponent<VerticalLayoutGroup>();
        ppVLG.spacing = 10;
        ppVLG.padding = new RectOffset(15, 15, 15, 15);
        ppVLG.childAlignment = TextAnchor.UpperCenter;
        ppVLG.childForceExpandWidth = true;
        ppVLG.childForceExpandHeight = false;
        ppVLG.childControlWidth = true;
        ppVLG.childControlHeight = false;
        var ppImg = playerPanel.AddComponent<Image>();
        ppImg.color = new Color(0.12f, 0.12f, 0.18f, 0.8f);

        var pNameGO = CreateTMPObject(playerPanel.transform, "PlayerMonsterName",
            "Your Monster", 24, TextAlignmentOptions.Center, Color.white, FontStyles.Bold);
        var pNameLE = pNameGO.AddComponent<LayoutElement>();
        pNameLE.preferredHeight = 35;

        var playerHpSlider = CreateSlider(playerPanel.transform, "PlayerHpBar",
            new Color(0.13f, 0.77f, 0.37f, 1f));
        var pSliderLE = playerHpSlider.gameObject.AddComponent<LayoutElement>();
        pSliderLE.preferredHeight = 30;

        var pHpGO = CreateTMPObject(playerPanel.transform, "PlayerHpText",
            "HP: 0/0", 16, TextAlignmentOptions.Center, Color.white, FontStyles.Normal);
        var pHpLE = pHpGO.AddComponent<LayoutElement>();
        pHpLE.preferredHeight = 25;

        // EnemyPanel (right)
        var enemyPanel = CreateUIObject("EnemyPanel", canvasT);
        var epRT = enemyPanel.GetComponent<RectTransform>();
        epRT.anchorMin = new Vector2(0.55f, 0.3f);
        epRT.anchorMax = new Vector2(1f, 0.9f);
        epRT.offsetMin = new Vector2(10, 0);
        epRT.offsetMax = new Vector2(-20, -10);
        var epVLG = enemyPanel.AddComponent<VerticalLayoutGroup>();
        epVLG.spacing = 10;
        epVLG.padding = new RectOffset(15, 15, 15, 15);
        epVLG.childAlignment = TextAnchor.UpperCenter;
        epVLG.childForceExpandWidth = true;
        epVLG.childForceExpandHeight = false;
        epVLG.childControlWidth = true;
        epVLG.childControlHeight = false;
        var epImg = enemyPanel.AddComponent<Image>();
        epImg.color = new Color(0.12f, 0.12f, 0.18f, 0.8f);

        var eNameGO = CreateTMPObject(enemyPanel.transform, "EnemyMonsterName",
            "Enemy Monster", 24, TextAlignmentOptions.Center, Color.white, FontStyles.Bold);
        var eNameLE = eNameGO.AddComponent<LayoutElement>();
        eNameLE.preferredHeight = 35;

        var enemyHpSlider = CreateSlider(enemyPanel.transform, "EnemyHpBar",
            new Color(0.94f, 0.27f, 0.27f, 1f));
        var eSliderLE = enemyHpSlider.gameObject.AddComponent<LayoutElement>();
        eSliderLE.preferredHeight = 30;

        var eHpGO = CreateTMPObject(enemyPanel.transform, "EnemyHpText",
            "HP: 0/0", 16, TextAlignmentOptions.Center, Color.white, FontStyles.Normal);
        var eHpLE = eHpGO.AddComponent<LayoutElement>();
        eHpLE.preferredHeight = 25;

        // CombatLogArea (bottom center)
        var logArea = CreateUIObject("CombatLogArea", canvasT);
        var logRT = logArea.GetComponent<RectTransform>();
        logRT.anchorMin = new Vector2(0.05f, 0.12f);
        logRT.anchorMax = new Vector2(0.95f, 0.28f);
        logRT.offsetMin = Vector2.zero;
        logRT.offsetMax = Vector2.zero;

        var combatLogScroll = CreateUIObject("CombatLogScroll", logArea.transform);
        var clsRT = combatLogScroll.GetComponent<RectTransform>();
        clsRT.anchorMin = Vector2.zero;
        clsRT.anchorMax = Vector2.one;
        clsRT.offsetMin = Vector2.zero;
        clsRT.offsetMax = Vector2.zero;
        var clsBg = combatLogScroll.AddComponent<Image>();
        clsBg.color = new Color(0.08f, 0.08f, 0.12f, 0.9f);
        var scrollRectComp = combatLogScroll.AddComponent<ScrollRect>();
        scrollRectComp.horizontal = false;

        var clsViewport = CreateUIObject("Viewport", combatLogScroll.transform);
        var clsVpRT = clsViewport.GetComponent<RectTransform>();
        clsVpRT.anchorMin = Vector2.zero;
        clsVpRT.anchorMax = Vector2.one;
        clsVpRT.offsetMin = new Vector2(5, 5);
        clsVpRT.offsetMax = new Vector2(-5, -5);
        clsViewport.AddComponent<Image>().color = Color.clear;
        clsViewport.AddComponent<Mask>().showMaskGraphic = false;

        var clsContent = CreateUIObject("Content", clsViewport.transform);
        var clsContentRT = clsContent.GetComponent<RectTransform>();
        clsContentRT.anchorMin = new Vector2(0, 1);
        clsContentRT.anchorMax = new Vector2(1, 1);
        clsContentRT.pivot = new Vector2(0.5f, 1f);
        clsContentRT.offsetMin = Vector2.zero;
        clsContentRT.offsetMax = Vector2.zero;
        var clsCSF = clsContent.AddComponent<ContentSizeFitter>();
        clsCSF.verticalFit = ContentSizeFitter.FitMode.PreferredSize;

        var combatLogTextGO = CreateTMPObject(clsContent.transform, "CombatLogText",
            "", 14, TextAlignmentOptions.TopLeft, Color.white, FontStyles.Normal);
        var logTextRT = combatLogTextGO.GetComponent<RectTransform>();
        logTextRT.anchorMin = Vector2.zero;
        logTextRT.anchorMax = new Vector2(1, 1);
        logTextRT.offsetMin = Vector2.zero;
        logTextRT.offsetMax = Vector2.zero;

        scrollRectComp.content = clsContentRT;
        scrollRectComp.viewport = clsVpRT;

        // StatusText (center)
        var statusGO = CreateTMPObject(canvasT, "StatusText", "Starting combat...", 20,
            TextAlignmentOptions.Center, Color.white, FontStyles.Normal);
        var statusRT = statusGO.GetComponent<RectTransform>();
        statusRT.anchorMin = new Vector2(0.5f, 0.5f);
        statusRT.anchorMax = new Vector2(0.5f, 0.5f);
        statusRT.sizeDelta = new Vector2(400, 50);
        statusRT.anchoredPosition = Vector2.zero;

        // NextRoundButton (bottom)
        var nextRoundBtn = CreateButtonWithText(
            canvasT, "NextRoundButton", "Next Round", 45,
            new Color(0.2f, 0.6f, 1f, 1f), new Color(0.3f, 0.7f, 1f, 1f));
        var nrRT = nextRoundBtn.GetComponent<RectTransform>();
        nrRT.anchorMin = new Vector2(0.3f, 0.02f);
        nrRT.anchorMax = new Vector2(0.7f, 0.1f);
        nrRT.offsetMin = Vector2.zero;
        nrRT.offsetMax = Vector2.zero;

        // BackToHomeButton (starts inactive)
        var backBtn = CreateButtonWithText(
            canvasT, "BackToHomeButton", "Back to Home", 40,
            new Color(0.5f, 0.5f, 0.5f, 1f), new Color(0.6f, 0.6f, 0.6f, 1f));
        var bbRT = backBtn.GetComponent<RectTransform>();
        bbRT.anchorMin = new Vector2(0.3f, 0.02f);
        bbRT.anchorMax = new Vector2(0.7f, 0.1f);
        bbRT.offsetMin = Vector2.zero;
        bbRT.offsetMax = Vector2.zero;
        backBtn.SetActive(false);

        // CombatController
        var controllerGO = new GameObject("CombatController");
        var combatCtrl = controllerGO.AddComponent<CombatController>();

        SetPrivateField(combatCtrl, "playerMonsterName",
            pNameGO.GetComponent<TextMeshProUGUI>());
        SetPrivateField(combatCtrl, "playerHpBar", playerHpSlider);
        SetPrivateField(combatCtrl, "playerHpText",
            pHpGO.GetComponent<TextMeshProUGUI>());
        SetPrivateField(combatCtrl, "enemyMonsterName",
            eNameGO.GetComponent<TextMeshProUGUI>());
        SetPrivateField(combatCtrl, "enemyHpBar", enemyHpSlider);
        SetPrivateField(combatCtrl, "enemyHpText",
            eHpGO.GetComponent<TextMeshProUGUI>());
        SetPrivateField(combatCtrl, "combatLogText",
            combatLogTextGO.GetComponent<TextMeshProUGUI>());
        SetPrivateField(combatCtrl, "combatLogScroll", scrollRectComp);
        SetPrivateField(combatCtrl, "nextRoundButton",
            nextRoundBtn.GetComponent<Button>());
        SetPrivateField(combatCtrl, "statusText",
            statusGO.GetComponent<TextMeshProUGUI>());
        SetPrivateField(combatCtrl, "backToHomeButton",
            backBtn.GetComponent<Button>());

        EditorSceneManager.SaveScene(scene, $"{ScenesFolder}/Combat.unity");
        Debug.Log("[ElementsRPG] Created Combat scene.");
    }

    // ----------------------------------------------------------------
    // Step 7: Results Scene
    // ----------------------------------------------------------------

    private static void CreateResultsScene()
    {
        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

        CreateEventSystem();
        var canvas = CreateCanvas("Canvas");
        var canvasT = canvas.transform;

        // ResultsPanel (center)
        var panel = CreateUIObject("ResultsPanel", canvasT);
        var panelRT = panel.GetComponent<RectTransform>();
        panelRT.anchorMin = new Vector2(0.5f, 0.5f);
        panelRT.anchorMax = new Vector2(0.5f, 0.5f);
        panelRT.pivot = new Vector2(0.5f, 0.5f);
        panelRT.sizeDelta = new Vector2(500, 400);
        panelRT.anchoredPosition = Vector2.zero;

        var panelImg = panel.AddComponent<Image>();
        panelImg.color = new Color(0.12f, 0.12f, 0.18f, 1f);

        var vlg = panel.AddComponent<VerticalLayoutGroup>();
        vlg.spacing = 15;
        vlg.padding = new RectOffset(30, 30, 30, 30);
        vlg.childAlignment = TextAnchor.UpperCenter;
        vlg.childForceExpandWidth = true;
        vlg.childForceExpandHeight = false;
        vlg.childControlWidth = true;
        vlg.childControlHeight = false;

        // OutcomeText
        var outcomeGO = CreateTMPObject(panel.transform, "OutcomeText", "Victory!", 48,
            TextAlignmentOptions.Center, Color.green, FontStyles.Bold);
        var outcomeLE = outcomeGO.AddComponent<LayoutElement>();
        outcomeLE.preferredHeight = 60;

        // RoundsText
        var roundsGO = CreateTMPObject(panel.transform, "RoundsText", "Rounds: 0", 24,
            TextAlignmentOptions.Center, Color.white, FontStyles.Normal);
        var roundsLE = roundsGO.AddComponent<LayoutElement>();
        roundsLE.preferredHeight = 35;

        // XpText
        var xpGO = CreateTMPObject(panel.transform, "XpText", "XP Earned: 0", 24,
            TextAlignmentOptions.Center, Color.white, FontStyles.Normal);
        var xpLE = xpGO.AddComponent<LayoutElement>();
        xpLE.preferredHeight = 35;

        // GoldText
        var goldGO = CreateTMPObject(panel.transform, "GoldText", "Gold Earned: 0", 24,
            TextAlignmentOptions.Center, Color.white, FontStyles.Normal);
        var goldLE = goldGO.AddComponent<LayoutElement>();
        goldLE.preferredHeight = 35;

        // Spacer
        var spacer = CreateUIObject("Spacer", panel.transform);
        var spacerLE = spacer.AddComponent<LayoutElement>();
        spacerLE.preferredHeight = 30;

        // ContinueButton
        var continueBtn = CreateButtonWithText(
            panel.transform, "ContinueButton", "Continue", 45,
            new Color(0.2f, 0.6f, 1f, 1f), new Color(0.3f, 0.7f, 1f, 1f));

        // StatusText (starts inactive)
        var statusGO = CreateTMPObject(panel.transform, "StatusText", "", 16,
            TextAlignmentOptions.Center, Color.white, FontStyles.Normal);
        var statusLE = statusGO.AddComponent<LayoutElement>();
        statusLE.preferredHeight = 25;
        statusGO.SetActive(false);

        // ResultsController
        var controllerGO = new GameObject("ResultsController");
        var resultsCtrl = controllerGO.AddComponent<ResultsController>();

        SetPrivateField(resultsCtrl, "outcomeText",
            outcomeGO.GetComponent<TextMeshProUGUI>());
        SetPrivateField(resultsCtrl, "roundsText",
            roundsGO.GetComponent<TextMeshProUGUI>());
        SetPrivateField(resultsCtrl, "xpText",
            xpGO.GetComponent<TextMeshProUGUI>());
        SetPrivateField(resultsCtrl, "goldText",
            goldGO.GetComponent<TextMeshProUGUI>());
        SetPrivateField(resultsCtrl, "continueButton",
            continueBtn.GetComponent<Button>());
        SetPrivateField(resultsCtrl, "statusText",
            statusGO.GetComponent<TextMeshProUGUI>());

        EditorSceneManager.SaveScene(scene, $"{ScenesFolder}/Results.unity");
        Debug.Log("[ElementsRPG] Created Results scene.");
    }

    // ----------------------------------------------------------------
    // Step 8: Build Settings
    // ----------------------------------------------------------------

    private static void ConfigureBuildSettings()
    {
        var scenes = new EditorBuildSettingsScene[]
        {
            new EditorBuildSettingsScene($"{ScenesFolder}/Login.unity", true),
            new EditorBuildSettingsScene($"{ScenesFolder}/Home.unity", true),
            new EditorBuildSettingsScene($"{ScenesFolder}/Combat.unity", true),
            new EditorBuildSettingsScene($"{ScenesFolder}/Results.unity", true),
        };
        EditorBuildSettings.scenes = scenes;
        Debug.Log("[ElementsRPG] Build Settings configured (Login=0, Home=1, " +
                  "Combat=2, Results=3).");
    }

    // ================================================================
    // Helpers
    // ================================================================

    /// <summary>
    /// Sets a private serialized field on a MonoBehaviour using SerializedObject.
    /// This is the proper way to set [SerializeField] private fields in editor scripts.
    /// </summary>
    private static void SetPrivateField(MonoBehaviour target, string fieldName, Object value)
    {
        var so = new SerializedObject(target);
        var prop = so.FindProperty(fieldName);
        if (prop != null)
        {
            prop.objectReferenceValue = value;
            so.ApplyModifiedPropertiesWithoutUndo();
        }
        else
        {
            Debug.LogWarning(
                $"[ElementsRPG] Could not find serialized field '{fieldName}' " +
                $"on {target.GetType().Name}");
        }
    }

    /// <summary>Creates a singleton GameObject with DontDestroyOnLoad component.</summary>
    private static GameObject CreateSingleton<T>(string name) where T : MonoBehaviour
    {
        var go = new GameObject(name);
        go.AddComponent<T>();
        return go;
    }

    /// <summary>Creates a standard EventSystem with StandaloneInputModule.</summary>
    private static GameObject CreateEventSystem()
    {
        var go = new GameObject("EventSystem");
        go.AddComponent<EventSystem>();
        go.AddComponent<StandaloneInputModule>();
        return go;
    }

    /// <summary>Creates a Canvas with CanvasScaler and GraphicRaycaster.</summary>
    private static GameObject CreateCanvas(string name)
    {
        var go = new GameObject(name);
        var canvas = go.AddComponent<Canvas>();
        canvas.renderMode = RenderMode.ScreenSpaceOverlay;

        var scaler = go.AddComponent<CanvasScaler>();
        scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
        scaler.referenceResolution = new Vector2(1280, 720);
        scaler.matchWidthOrHeight = 0.5f;

        go.AddComponent<GraphicRaycaster>();
        return go;
    }

    /// <summary>Creates a GameObject with a RectTransform.</summary>
    private static GameObject CreateUIObject(string name, Transform parent)
    {
        var go = new GameObject(name);
        go.transform.SetParent(parent, false);
        go.AddComponent<RectTransform>();
        return go;
    }

    /// <summary>Creates a TextMeshProUGUI GameObject.</summary>
    private static GameObject CreateTMPObject(
        Transform parent, string name, string text, float fontSize,
        TextAlignmentOptions alignment, Color color, FontStyles fontStyle)
    {
        var go = new GameObject(name);
        go.transform.SetParent(parent, false);
        go.AddComponent<RectTransform>();
        var tmp = go.AddComponent<TextMeshProUGUI>();
        tmp.text = text;
        tmp.fontSize = fontSize;
        tmp.alignment = alignment;
        tmp.color = color;
        tmp.fontStyle = fontStyle;
        return go;
    }

    /// <summary>
    /// Creates a TMP_InputField with proper child hierarchy:
    /// Root (Image + TMP_InputField) > Text Area (RectMask2D) >
    ///   Placeholder (TMP) + Text (TMP).
    /// </summary>
    private static GameObject CreateTMPInputField(
        Transform parent, string name, string placeholderText, float height)
    {
        var go = new GameObject(name);
        go.transform.SetParent(parent, false);
        var rt = go.AddComponent<RectTransform>();
        rt.sizeDelta = new Vector2(0, height);

        var bg = go.AddComponent<Image>();
        bg.color = new Color(0.2f, 0.2f, 0.25f, 1f);

        var inputField = go.AddComponent<TMP_InputField>();

        var le = go.AddComponent<LayoutElement>();
        le.preferredHeight = height;

        // Text Area
        var textArea = new GameObject("Text Area");
        textArea.transform.SetParent(go.transform, false);
        var taRT = textArea.AddComponent<RectTransform>();
        taRT.anchorMin = Vector2.zero;
        taRT.anchorMax = Vector2.one;
        taRT.offsetMin = new Vector2(10, 0);
        taRT.offsetMax = new Vector2(-10, 0);
        textArea.AddComponent<RectMask2D>();

        // Placeholder
        var placeholderGO = new GameObject("Placeholder");
        placeholderGO.transform.SetParent(textArea.transform, false);
        var phRT = placeholderGO.AddComponent<RectTransform>();
        phRT.anchorMin = Vector2.zero;
        phRT.anchorMax = Vector2.one;
        phRT.offsetMin = Vector2.zero;
        phRT.offsetMax = Vector2.zero;
        var placeholderTMP = placeholderGO.AddComponent<TextMeshProUGUI>();
        placeholderTMP.text = placeholderText;
        placeholderTMP.fontSize = 16;
        placeholderTMP.fontStyle = FontStyles.Italic;
        placeholderTMP.color = new Color(0.6f, 0.6f, 0.6f, 1f);
        placeholderTMP.alignment = TextAlignmentOptions.MidlineLeft;

        // Input Text
        var textGO = new GameObject("Text");
        textGO.transform.SetParent(textArea.transform, false);
        var textObjRT = textGO.AddComponent<RectTransform>();
        textObjRT.anchorMin = Vector2.zero;
        textObjRT.anchorMax = Vector2.one;
        textObjRT.offsetMin = Vector2.zero;
        textObjRT.offsetMax = Vector2.zero;
        var inputText = textGO.AddComponent<TextMeshProUGUI>();
        inputText.text = "";
        inputText.fontSize = 16;
        inputText.color = Color.white;
        inputText.alignment = TextAlignmentOptions.MidlineLeft;

        // Wire TMP_InputField references
        inputField.textViewport = taRT;
        inputField.textComponent = inputText;
        inputField.placeholder = placeholderTMP;

        return go;
    }

    /// <summary>
    /// Creates a Button with Image + child TextMeshProUGUI.
    /// </summary>
    private static GameObject CreateButtonWithText(
        Transform parent, string name, string buttonText, float height,
        Color normalColor, Color highlightedColor)
    {
        var go = new GameObject(name);
        go.transform.SetParent(parent, false);
        var rt = go.AddComponent<RectTransform>();
        rt.sizeDelta = new Vector2(0, height);

        var img = go.AddComponent<Image>();
        img.color = normalColor;

        var btn = go.AddComponent<Button>();
        var colors = btn.colors;
        colors.normalColor = normalColor;
        colors.highlightedColor = highlightedColor;
        colors.pressedColor = highlightedColor * 0.9f;
        colors.selectedColor = highlightedColor;
        btn.colors = colors;
        btn.targetGraphic = img;

        var le = go.AddComponent<LayoutElement>();
        le.preferredHeight = height;

        // Button label
        var textGO = new GameObject("Text");
        textGO.transform.SetParent(go.transform, false);
        var textRT = textGO.AddComponent<RectTransform>();
        textRT.anchorMin = Vector2.zero;
        textRT.anchorMax = Vector2.one;
        textRT.offsetMin = Vector2.zero;
        textRT.offsetMax = Vector2.zero;
        var tmp = textGO.AddComponent<TextMeshProUGUI>();
        tmp.text = buttonText;
        tmp.fontSize = 18;
        tmp.alignment = TextAlignmentOptions.Center;
        tmp.color = Color.white;

        return go;
    }

    /// <summary>
    /// Creates a UI Slider suitable for an HP bar (no handle, custom fill color).
    /// </summary>
    private static Slider CreateSlider(Transform parent, string name, Color fillColor)
    {
        var go = new GameObject(name);
        go.transform.SetParent(parent, false);
        var rt = go.AddComponent<RectTransform>();
        rt.sizeDelta = new Vector2(0, 30);

        // Background
        var bgGO = new GameObject("Background");
        bgGO.transform.SetParent(go.transform, false);
        var bgRT = bgGO.AddComponent<RectTransform>();
        bgRT.anchorMin = Vector2.zero;
        bgRT.anchorMax = Vector2.one;
        bgRT.offsetMin = Vector2.zero;
        bgRT.offsetMax = Vector2.zero;
        var bgImg = bgGO.AddComponent<Image>();
        bgImg.color = new Color(0.15f, 0.15f, 0.2f, 1f);

        // Fill Area
        var fillArea = new GameObject("Fill Area");
        fillArea.transform.SetParent(go.transform, false);
        var faRT = fillArea.AddComponent<RectTransform>();
        faRT.anchorMin = Vector2.zero;
        faRT.anchorMax = Vector2.one;
        faRT.offsetMin = Vector2.zero;
        faRT.offsetMax = Vector2.zero;

        // Fill
        var fillGO = new GameObject("Fill");
        fillGO.transform.SetParent(fillArea.transform, false);
        var fillRT = fillGO.AddComponent<RectTransform>();
        fillRT.anchorMin = Vector2.zero;
        fillRT.anchorMax = new Vector2(1, 1);
        fillRT.offsetMin = Vector2.zero;
        fillRT.offsetMax = Vector2.zero;
        var fillImg = fillGO.AddComponent<Image>();
        fillImg.color = fillColor;

        // Slider component
        var slider = go.AddComponent<Slider>();
        slider.fillRect = fillRT;
        slider.targetGraphic = fillImg;
        slider.direction = Slider.Direction.LeftToRight;
        slider.minValue = 0;
        slider.maxValue = 100;
        slider.value = 100;
        slider.wholeNumbers = false;

        // No handle (HP bars don't need one)
        slider.handleRect = null;

        return slider;
    }

    /// <summary>Anchors a RectTransform to stretch across the top with given height.</summary>
    private static void SetAnchorStretchTop(RectTransform rt, float height)
    {
        rt.anchorMin = new Vector2(0, 1);
        rt.anchorMax = new Vector2(1, 1);
        rt.pivot = new Vector2(0.5f, 1f);
        rt.offsetMin = new Vector2(0, -height);
        rt.offsetMax = Vector2.zero;
    }

    /// <summary>Anchors a RectTransform to stretch across the bottom with given height.</summary>
    private static void SetAnchorStretchBottom(RectTransform rt, float height)
    {
        rt.anchorMin = new Vector2(0, 0);
        rt.anchorMax = new Vector2(1, 0);
        rt.pivot = new Vector2(0.5f, 0f);
        rt.offsetMin = Vector2.zero;
        rt.offsetMax = new Vector2(0, height);
    }

    /// <summary>
    /// Rebuilds WebGL to the webgl-build folder at the repo root.
    /// Run via: ElementsRPG > Build WebGL
    /// </summary>
    [MenuItem("ElementsRPG/Build WebGL")]
    public static void BuildWebGL()
    {
        // Get repo root (one level up from the Unity project)
        string repoRoot = Path.GetFullPath(Path.Combine(Application.dataPath, "..", ".."));
        string buildPath = Path.Combine(repoRoot, "webgl-build");

        // Ensure output directory exists
        if (!Directory.Exists(buildPath))
            Directory.CreateDirectory(buildPath);

        // Get scenes from build settings
        var scenes = new string[EditorBuildSettings.scenes.Length];
        for (int i = 0; i < EditorBuildSettings.scenes.Length; i++)
            scenes[i] = EditorBuildSettings.scenes[i].path;

        if (scenes.Length == 0)
        {
            Debug.LogError("[ElementsRPG] No scenes in Build Settings! Run 'ElementsRPG > Setup Project' first.");
            return;
        }

        Debug.Log($"[ElementsRPG] Building WebGL to: {buildPath}");

        var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions
        {
            scenes = scenes,
            locationPathName = buildPath,
            target = BuildTarget.WebGL,
            options = BuildOptions.None
        });

        if (report.summary.result == UnityEditor.Build.Reporting.BuildResult.Succeeded)
            Debug.Log($"[ElementsRPG] WebGL build succeeded! Size: {report.summary.totalSize / (1024 * 1024)}MB. Output: {buildPath}");
        else
            Debug.LogError($"[ElementsRPG] WebGL build failed: {report.summary.result}");
    }

    /// <summary>
    /// Runs Setup Project then Build WebGL in sequence.
    /// Run via: ElementsRPG > Setup + Build WebGL
    /// </summary>
    [MenuItem("ElementsRPG/Setup + Build WebGL")]
    public static void SetupAndBuild()
    {
        SetupProject();
        BuildWebGL();
    }
}
