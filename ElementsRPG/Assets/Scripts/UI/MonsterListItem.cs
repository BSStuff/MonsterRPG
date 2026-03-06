using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using TMPro;

/// <summary>
/// Controller for the monster row prefab in the Home scene scroll list.
/// Displays monster name, level, element type, and a colored element icon.
/// </summary>
public class MonsterListItem : MonoBehaviour
{
    [SerializeField] private Image elementIcon;
    [SerializeField] private TMP_Text nameText;
    [SerializeField] private TMP_Text levelText;
    [SerializeField] private TMP_Text typeText;

    private static readonly Dictionary<string, Color> ElementColors =
        new Dictionary<string, Color>
        {
            { "water", new Color(0.23f, 0.51f, 0.96f) },
            { "fire", new Color(0.94f, 0.27f, 0.27f) },
            { "grass", new Color(0.13f, 0.77f, 0.37f) },
            { "electric", new Color(0.92f, 0.70f, 0.03f) },
            { "wind", new Color(0.64f, 0.90f, 0.21f) },
            { "ground", new Color(0.57f, 0.25f, 0.05f) },
            { "rock", new Color(0.47f, 0.44f, 0.42f) },
            { "dark", new Color(0.42f, 0.13f, 0.66f) },
            { "light", new Color(0.99f, 0.88f, 0.28f) },
            { "ice", new Color(0.40f, 0.91f, 0.98f) },
        };

    /// <summary>
    /// Populates the list item with monster data.
    /// </summary>
    /// <param name="monsterName">Display name of the monster species.</param>
    /// <param name="level">Current monster level.</param>
    /// <param name="primaryElement">Primary element type (lowercase).</param>
    public void Setup(string monsterName, int level, string primaryElement)
    {
        nameText.text = monsterName;
        levelText.text = $"Lv.{level}";

        string displayElement = CapitalizeFirst(primaryElement);
        typeText.text = displayElement;

        Color elementColor = ElementColors.ContainsKey(primaryElement)
            ? ElementColors[primaryElement]
            : Color.white;

        elementIcon.color = elementColor;
        typeText.color = elementColor;
    }

    private static string CapitalizeFirst(string input)
    {
        if (string.IsNullOrEmpty(input))
        {
            return input;
        }

        return char.ToUpper(input[0]) + input.Substring(1);
    }
}
