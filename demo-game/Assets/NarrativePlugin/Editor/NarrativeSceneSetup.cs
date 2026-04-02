using UnityEngine;
using UnityEngine.UI;
using UnityEditor;
using TMPro;

/// <summary>
/// Editor utility — creates the full NarrativeSystem scene hierarchy in one click.
///
/// Usage: top menu → NarrativePlugin → Setup Scene
///
/// What it creates:
///   NarrativeSystem  (PlayerDataLogger, NarrativeManager, ContentInjector,
///                     TelemetryHooks, ExplorationTracker)
///   NarrativeCanvas  (Canvas → Panel → SpeakerLabel + BodyText)
///                     NarrativeUI wired to ContentInjector events
///
/// After running:
///   1. Assign your PluginConfig asset to PlayerDataLogger and NarrativeManager
///   2. Press Play and verify telemetry reaches the backend
/// </summary>
public static class NarrativeSceneSetup
{
    [MenuItem("NarrativePlugin/Setup Scene")]
    public static void SetupScene()
    {
        // ── NarrativeSystem GameObject ────────────────────────────────────
        var sysGO = new GameObject("NarrativeSystem");
        Undo.RegisterCreatedObjectUndo(sysGO, "Create NarrativeSystem");

        var logger    = sysGO.AddComponent<PlayerDataLogger>();
        var injector  = sysGO.AddComponent<ContentInjector>();
        var manager   = sysGO.AddComponent<NarrativeManager>();
        var hooks     = sysGO.AddComponent<TelemetryHooks>();
        var explorer  = sysGO.AddComponent<ExplorationTracker>();

        // Wire NarrativeManager internal references via SerializedObject
        var managerSO = new SerializedObject(manager);
        managerSO.FindProperty("injector").objectReferenceValue = injector;
        managerSO.FindProperty("logger").objectReferenceValue   = logger;
        managerSO.ApplyModifiedProperties();

        var hooksSO = new SerializedObject(hooks);
        hooksSO.FindProperty("logger").objectReferenceValue           = logger;
        hooksSO.FindProperty("narrativeManager").objectReferenceValue = manager;
        hooksSO.ApplyModifiedProperties();

        var explorerSO = new SerializedObject(explorer);
        explorerSO.FindProperty("logger").objectReferenceValue = logger;
        explorerSO.ApplyModifiedProperties();

        // ── NarrativeCanvas ───────────────────────────────────────────────
        var canvasGO = new GameObject("NarrativeCanvas");
        Undo.RegisterCreatedObjectUndo(canvasGO, "Create NarrativeCanvas");

        var canvas = canvasGO.AddComponent<Canvas>();
        canvas.renderMode = RenderMode.ScreenSpaceOverlay;
        canvas.sortingOrder = 100;
        canvasGO.AddComponent<CanvasScaler>();
        canvasGO.AddComponent<GraphicRaycaster>();

        // Backdrop panel
        var panelGO = new GameObject("NarrativePanel");
        panelGO.transform.SetParent(canvasGO.transform, false);
        var panelImage = panelGO.AddComponent<Image>();
        panelImage.color = new Color(0f, 0f, 0f, 0.72f);

        var panelRect = panelGO.GetComponent<RectTransform>();
        panelRect.anchorMin        = new Vector2(0.1f, 0.05f);
        panelRect.anchorMax        = new Vector2(0.9f, 0.28f);
        panelRect.offsetMin        = Vector2.zero;
        panelRect.offsetMax        = Vector2.zero;

        // Speaker label
        var speakerGO   = new GameObject("SpeakerLabel");
        speakerGO.transform.SetParent(panelGO.transform, false);
        var speakerTMP  = speakerGO.AddComponent<TextMeshProUGUI>();
        speakerTMP.text      = "Speaker";
        speakerTMP.fontSize  = 18f;
        speakerTMP.fontStyle = FontStyles.Bold;
        speakerTMP.color     = Color.white;
        var speakerRect = speakerGO.GetComponent<RectTransform>();
        speakerRect.anchorMin  = new Vector2(0f, 0.7f);
        speakerRect.anchorMax  = new Vector2(1f, 1f);
        speakerRect.offsetMin  = new Vector2(12f, 0f);
        speakerRect.offsetMax  = new Vector2(-12f, 0f);

        // Body text
        var bodyGO  = new GameObject("BodyText");
        bodyGO.transform.SetParent(panelGO.transform, false);
        var bodyTMP = bodyGO.AddComponent<TextMeshProUGUI>();
        bodyTMP.text         = "Narrative text will appear here…";
        bodyTMP.fontSize     = 15f;
        bodyTMP.color        = new Color(0.9f, 0.85f, 0.6f);
        bodyTMP.enableWordWrapping = true;
        var bodyRect = bodyGO.GetComponent<RectTransform>();
        bodyRect.anchorMin  = new Vector2(0f, 0f);
        bodyRect.anchorMax  = new Vector2(1f, 0.7f);
        bodyRect.offsetMin  = new Vector2(12f, 8f);
        bodyRect.offsetMax  = new Vector2(-12f, 0f);

        // NarrativeUI component
        var uiComp = canvasGO.AddComponent<NarrativeUI>();
        var uiSO   = new SerializedObject(uiComp);
        uiSO.FindProperty("panel").objectReferenceValue        = panelGO;
        uiSO.FindProperty("speakerLabel").objectReferenceValue = speakerTMP;
        uiSO.FindProperty("bodyText").objectReferenceValue     = bodyTMP;
        uiSO.ApplyModifiedProperties();

        // Wire ContentInjector UnityEvents → NarrativeUI methods
        // (programmatic UnityEvent wiring)
        WireUnityEvent(injector, "OnDialogueInjected",  uiComp, "ShowDialogue");
        WireUnityEvent(injector, "OnDescriptionInjected", uiComp, "ShowDescription");
        WireUnityEvent(injector, "OnQuestUpdateInjected", uiComp, "ShowQuestUpdate");

        // ── Select NarrativeSystem in hierarchy ───────────────────────────
        Selection.activeGameObject = sysGO;

        Debug.Log("[NarrativePlugin] Scene setup complete.\n" +
                  "ACTION REQUIRED: Assign your PluginConfig asset to:\n" +
                  "  • NarrativeSystem → PlayerDataLogger → Config\n" +
                  "  • NarrativeSystem → NarrativeManager → Config");
    }

    private static void WireUnityEvent(Component target, string eventPropertyName,
                                       Component listener, string methodName)
    {
        var so    = new SerializedObject(target);
        var evProp = so.FindProperty(eventPropertyName);
        if (evProp == null) return;

        var callsProp = evProp.FindPropertyRelative("m_PersistentCalls.m_Calls");
        callsProp.InsertArrayElementAtIndex(0);
        var call = callsProp.GetArrayElementAtIndex(0);

        call.FindPropertyRelative("m_Target").objectReferenceValue     = listener;
        call.FindPropertyRelative("m_MethodName").stringValue          = methodName;
        call.FindPropertyRelative("m_Mode").enumValueIndex             = 1; // EventDefined
        call.FindPropertyRelative("m_CallState").enumValueIndex        = 2; // RuntimeOnly

        so.ApplyModifiedProperties();
    }

    [MenuItem("NarrativePlugin/Setup Scene", true)]
    private static bool ValidateSetupScene()
    {
        // Only enabled when a scene is open
        return UnityEngine.SceneManagement.SceneManager.GetActiveScene().IsValid();
    }
}
