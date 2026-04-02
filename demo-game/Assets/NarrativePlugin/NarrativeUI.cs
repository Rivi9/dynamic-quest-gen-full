using System.Collections;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// Displays incoming narrative text in a HUD panel.
/// Wire the three ContentInjector UnityEvents to the three public methods below:
///
///   ContentInjector.OnDialogueInjected  → NarrativeUI.ShowDialogue
///   ContentInjector.OnDescriptionInjected → NarrativeUI.ShowDescription
///   ContentInjector.OnQuestUpdateInjected → NarrativeUI.ShowQuestUpdate
///
/// The panel auto-dismisses after <see cref="displayDuration"/> seconds.
/// </summary>
public class NarrativeUI : MonoBehaviour
{
    [Header("Panel references")]
    [SerializeField] private GameObject     panel;
    [SerializeField] private TextMeshProUGUI speakerLabel;
    [SerializeField] private TextMeshProUGUI bodyText;

    [Header("Optional type-label colours")]
    [SerializeField] private Color dialogueColour     = new Color(0.9f, 0.85f, 0.6f);
    [SerializeField] private Color descriptionColour  = new Color(0.7f, 0.9f, 1.0f);
    [SerializeField] private Color questColour        = new Color(0.6f, 1.0f, 0.7f);

    [Header("Timing")]
    [Tooltip("Seconds before the panel automatically hides.")]
    [SerializeField] private float displayDuration = 8f;

    [Tooltip("Fade-out duration in seconds (0 = instant).")]
    [SerializeField] private float fadeDuration = 0.5f;

    private CanvasGroup _canvasGroup;
    private Coroutine   _hideRoutine;

    // ── Unity lifecycle ───────────────────────────────────────────────────

    private void Awake()
    {
        _canvasGroup = panel.GetComponent<CanvasGroup>();
        if (_canvasGroup == null)
            _canvasGroup = panel.AddComponent<CanvasGroup>();

        panel.SetActive(false);
    }

    // ── Public API — wire these to ContentInjector events ─────────────────

    /// <summary>Called by ContentInjector.OnDialogueInjected (speaker, text).</summary>
    public void ShowDialogue(string speaker, string text)
    {
        Show(speaker, text, dialogueColour);
    }

    /// <summary>Called by ContentInjector.OnDescriptionInjected (text).</summary>
    public void ShowDescription(string text)
    {
        Show("", text, descriptionColour);
    }

    /// <summary>Called by ContentInjector.OnQuestUpdateInjected (text).</summary>
    public void ShowQuestUpdate(string text)
    {
        Show("Quest Update", text, questColour);
    }

    /// <summary>Hide the panel immediately.</summary>
    public void Hide()
    {
        if (_hideRoutine != null) StopCoroutine(_hideRoutine);
        panel.SetActive(false);
    }

    // ── Internal ──────────────────────────────────────────────────────────

    private void Show(string speaker, string text, Color colour)
    {
        if (_hideRoutine != null) StopCoroutine(_hideRoutine);

        if (speakerLabel != null)
        {
            speakerLabel.text    = speaker;
            speakerLabel.gameObject.SetActive(!string.IsNullOrEmpty(speaker));
        }

        if (bodyText != null)
        {
            bodyText.text  = text;
            bodyText.color = colour;
        }

        _canvasGroup.alpha = 1f;
        panel.SetActive(true);

        _hideRoutine = StartCoroutine(AutoHide());
    }

    private IEnumerator AutoHide()
    {
        yield return new WaitForSeconds(displayDuration);

        if (fadeDuration > 0f)
        {
            float elapsed = 0f;
            while (elapsed < fadeDuration)
            {
                _canvasGroup.alpha = Mathf.Lerp(1f, 0f, elapsed / fadeDuration);
                elapsed += Time.deltaTime;
                yield return null;
            }
        }

        panel.SetActive(false);
        _canvasGroup.alpha = 1f;
    }
}
