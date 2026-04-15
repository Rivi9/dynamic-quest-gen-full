using System.Collections;
using AnyRPG;
using UnityEngine;
using UnityEngine.Networking;

[System.Serializable]
public class PlayerModelResponse
{
    public string player_id;
    public string session_id;
    public string current_state;
    public string flow_state;
    public float flow_score;
    public float challenge_skill_ratio;
    public HexadProfileResponse hexad_profile;
    public float session_elapsed;
}

[System.Serializable]
public class HexadProfileResponse
{
    public float achiever;
    public float explorer;
    public float socializer;
    public float free_spirit;
    public float disruptor;
    public float philanthropist;
}

/// <summary>
/// Pulls the current player model from the backend and updates the quest context
/// so different player types get visibly different narrative goals in the demo.
/// </summary>
public class QuestPersonalizationDirector : MonoBehaviour
{
    [SerializeField] private PluginConfig config;
    [SerializeField] private PlayerDataLogger logger;
    [SerializeField] private NarrativeManager narrativeManager;
    [SerializeField] private ContentInjector injector;
    [SerializeField] private SystemGameManager systemGameManager;
    [SerializeField] private NarrativeTriggerDirector triggerDirector;

    [Header("Polling")]
    [SerializeField] private float playerModelPollingInterval = 20f;
    [SerializeField] private float minimumSessionSeconds = 15f;

    [Header("Flow Overrides")]
    [SerializeField] private string boredomQuestStage = "Reports of movement on the ridge. Sweep the northern route for signs of escalation.";
    [SerializeField] private string anxietyQuestStage = "Hold the safer line and regroup with nearby allies before pressing forward.";
    [SerializeField] private string apathyQuestStage = "A strange omen lingers near the Vault. Investigate the source and recover your focus.";

    [Header("Hexad Quest Contexts")]
    [SerializeField] private string explorerQuestStage = "Investigate the old Vault markings and uncover what the Chronicler has not yet explained.";
    [SerializeField] private string socializerQuestStage = "Speak with Varis and the Chronicler to gather guidance before the next push.";
    [SerializeField] private string achieverQuestStage = "Secure the northern approach and complete the patrol objectives with minimal losses.";
    [SerializeField] private string disruptorQuestStage = "Break the enemy line with aggressive action before the Host can reorganize.";
    [SerializeField] private string freeSpiritQuestStage = "Scout beyond the main path and look for an alternate route around the contested centre.";
    [SerializeField] private string philanthropistQuestStage = "Aid the defenders and stabilize the line where the fighting is turning against them.";

    [Header("Quest Mapping")]
    [SerializeField] private bool acceptMappedQuestIntoQuestLog = true;
    [SerializeField] private string explorerQuestResource = "Visit Zone";
    [SerializeField] private string socializerQuestResource = "Dialog Objective";
    [SerializeField] private string achieverQuestResource = "Kill Things";
    [SerializeField] private string disruptorQuestResource = "Kill Things";
    [SerializeField] private string freeSpiritQuestResource = "Use Interactable";
    [SerializeField] private string philanthropistQuestResource = "Dialog Introduction";
    [SerializeField] private string anxietyQuestResource = "Dialog Introduction";
    [SerializeField] private string boredomQuestResource = "Kill Things";
    [SerializeField] private string apathyQuestResource = "Visit Zone";

    [Header("Combined Flow + Hexad Quest Mapping")]
    [SerializeField] private string anxietyExplorerQuestResource = "Visit Zone";
    [SerializeField] private string anxietySocializerQuestResource = "Dialog Introduction";
    [SerializeField] private string anxietyAchieverQuestResource = "Kill Things";
    [SerializeField] private string anxietyDisruptorQuestResource = "Kill Things";
    [SerializeField] private string anxietyFreeSpiritQuestResource = "Use Interactable";
    [SerializeField] private string anxietyPhilanthropistQuestResource = "Dialog Introduction";
    [SerializeField] private string boredomExplorerQuestResource = "Visit Zone";
    [SerializeField] private string boredomSocializerQuestResource = "Dialog Objective";
    [SerializeField] private string boredomAchieverQuestResource = "Kill Things";
    [SerializeField] private string boredomDisruptorQuestResource = "Kill Things";
    [SerializeField] private string boredomFreeSpiritQuestResource = "Use Interactable";
    [SerializeField] private string boredomPhilanthropistQuestResource = "Dialog Introduction";
    [SerializeField] private string apathyExplorerQuestResource = "Visit Zone";
    [SerializeField] private string apathySocializerQuestResource = "Dialog Objective";
    [SerializeField] private string apathyAchieverQuestResource = "Kill Things";
    [SerializeField] private string apathyDisruptorQuestResource = "Kill Things";
    [SerializeField] private string apathyFreeSpiritQuestResource = "Use Interactable";
    [SerializeField] private string apathyPhilanthropistQuestResource = "Dialog Introduction";

    private string _lastQuestStage;
    private string _lastAssignedQuestResource;

    private void Start()
    {
        if (logger == null)
            logger = FindObjectOfType<PlayerDataLogger>();

        if (narrativeManager == null)
            narrativeManager = FindObjectOfType<NarrativeManager>();

        if (injector == null)
            injector = FindObjectOfType<ContentInjector>();

        if (systemGameManager == null)
            systemGameManager = FindObjectOfType<SystemGameManager>();

        if (triggerDirector == null)
            triggerDirector = FindObjectOfType<NarrativeTriggerDirector>();

        if (logger == null || narrativeManager == null)
        {
            Debug.LogWarning("[QuestPersonalizationDirector] Missing logger or NarrativeManager; disabling.");
            enabled = false;
            return;
        }

        InvokeRepeating(nameof(RequestPlayerModel), playerModelPollingInterval, playerModelPollingInterval);
    }

    private void OnDestroy()
    {
        CancelInvoke(nameof(RequestPlayerModel));
        StopAllCoroutines();
    }

    private void RequestPlayerModel()
    {
        if (logger == null || string.IsNullOrEmpty(logger.SessionId))
            return;

        StartCoroutine(FetchPlayerModel());
    }

    private IEnumerator FetchPlayerModel()
    {
        var apiBaseUrl = ResolveApiBaseUrl();
        if (string.IsNullOrEmpty(apiBaseUrl))
            yield break;

        var url = $"{apiBaseUrl}/player-model/{logger.SessionId}?player_id={UnityWebRequest.EscapeURL(ResolvePlayerId())}";
        var webReq = UnityWebRequest.Get(url);
        yield return webReq.SendWebRequest();

        if (webReq.result != UnityWebRequest.Result.Success)
        {
            Debug.LogWarning($"[QuestPersonalizationDirector] Player model request failed: {webReq.error}");
            webReq.Dispose();
            yield break;
        }

        var response = JsonUtility.FromJson<PlayerModelResponse>(webReq.downloadHandler.text);
        if (response == null || response.hexad_profile == null)
        {
            webReq.Dispose();
            yield break;
        }

        if (response.session_elapsed < minimumSessionSeconds)
        {
            webReq.Dispose();
            yield break;
        }

        var dominantHexad = GetDominantHexad(response.hexad_profile);
        var nextQuestStage = BuildQuestStage(response, dominantHexad);
        if (string.IsNullOrWhiteSpace(nextQuestStage) || nextQuestStage == _lastQuestStage)
        {
            webReq.Dispose();
            yield break;
        }

        _lastQuestStage = nextQuestStage;
        narrativeManager.currentQuestStage = nextQuestStage;
        TryAssignMappedQuest(response, dominantHexad);
        triggerDirector?.TriggerQuestUpdate($"player_model_{response.flow_state.ToLower()}_{dominantHexad}");
        Debug.Log($"[QuestPersonalizationDirector] Dominant model => {response.flow_state} / {dominantHexad}. Quest context updated to: {nextQuestStage}");
        webReq.Dispose();
    }

    private string BuildQuestStage(PlayerModelResponse response, string dominantHexad)
    {
        string flowStage = null;
        switch (response.flow_state)
        {
            case "ANXIETY":
                flowStage = anxietyQuestStage;
                break;
            case "BOREDOM":
                flowStage = boredomQuestStage;
                break;
            case "APATHY":
                flowStage = apathyQuestStage;
                break;
        }

        string hexadStage = dominantHexad switch
        {
            "explorer" => explorerQuestStage,
            "socializer" => socializerQuestStage,
            "achiever" => achieverQuestStage,
            "disruptor" => disruptorQuestStage,
            "free_spirit" => freeSpiritQuestStage,
            "philanthropist" => philanthropistQuestStage,
            _ => narrativeManager.currentQuestStage
        };

        if (!string.IsNullOrWhiteSpace(flowStage))
            return $"{flowStage} Priority style: {hexadStage}";

        return hexadStage;
    }

    private string GetDominantHexad(HexadProfileResponse hexad)
    {
        var bestKey = "explorer";
        var bestValue = hexad.explorer;

        Consider("socializer", hexad.socializer, ref bestKey, ref bestValue);
        Consider("achiever", hexad.achiever, ref bestKey, ref bestValue);
        Consider("disruptor", hexad.disruptor, ref bestKey, ref bestValue);
        Consider("free_spirit", hexad.free_spirit, ref bestKey, ref bestValue);
        Consider("philanthropist", hexad.philanthropist, ref bestKey, ref bestValue);

        return bestKey;
    }

    private void Consider(string key, float value, ref string bestKey, ref float bestValue)
    {
        if (value > bestValue)
        {
            bestKey = key;
            bestValue = value;
        }
    }

    private string ResolveApiBaseUrl()
    {
        if (config != null && !string.IsNullOrWhiteSpace(config.backendApiUrl))
            return config.backendApiUrl;

        return "http://localhost:8000/api";
    }

    private string ResolvePlayerId()
    {
        if (config != null && !string.IsNullOrWhiteSpace(config.playerId))
            return config.playerId;

        return "player_001";
    }

    private void TryAssignMappedQuest(PlayerModelResponse response, string dominantHexad)
    {
        if (!acceptMappedQuestIntoQuestLog || systemGameManager?.QuestLog == null || systemGameManager.SystemDataFactory == null)
            return;

        var questResource = GetMappedQuestResource(response.flow_state, dominantHexad);
        if (string.IsNullOrWhiteSpace(questResource) || questResource == _lastAssignedQuestResource)
            return;

        var quest = systemGameManager.SystemDataFactory.GetResource<Quest>(questResource);
        if (quest == null)
            return;

        if (systemGameManager.QuestLog.HasQuest(quest.ResourceName))
        {
            _lastAssignedQuestResource = quest.ResourceName;
            return;
        }

        systemGameManager.QuestLog.AcceptQuest(quest);

        systemGameManager.QuestLog.ShowQuestLogDescription(quest);
        _lastAssignedQuestResource = quest.ResourceName;

        if (injector != null)
        {
            injector.Apply(new NarrativeResponse
            {
                action_taken = "QUEST_PERSONALIZATION",
                content_type = "quest_update",
                content = $"Personalized quest: {quest.DisplayName}",
                speaker = null,
                emotional_tone = "neutral",
                fallback = false
            });
        }

        Debug.Log($"[QuestPersonalizationDirector] Assigned real quest from AnyRPG QuestLog: {quest.DisplayName} ({quest.ResourceName})");
    }

    private string GetMappedQuestResource(string flowState, string dominantHexad)
    {
        switch (flowState)
        {
            case "ANXIETY":
                return GetCombinedFlowQuestResource(
                    dominantHexad,
                    anxietyExplorerQuestResource,
                    anxietySocializerQuestResource,
                    anxietyAchieverQuestResource,
                    anxietyDisruptorQuestResource,
                    anxietyFreeSpiritQuestResource,
                    anxietyPhilanthropistQuestResource,
                    anxietyQuestResource
                );
            case "BOREDOM":
                return GetCombinedFlowQuestResource(
                    dominantHexad,
                    boredomExplorerQuestResource,
                    boredomSocializerQuestResource,
                    boredomAchieverQuestResource,
                    boredomDisruptorQuestResource,
                    boredomFreeSpiritQuestResource,
                    boredomPhilanthropistQuestResource,
                    boredomQuestResource
                );
            case "APATHY":
                return GetCombinedFlowQuestResource(
                    dominantHexad,
                    apathyExplorerQuestResource,
                    apathySocializerQuestResource,
                    apathyAchieverQuestResource,
                    apathyDisruptorQuestResource,
                    apathyFreeSpiritQuestResource,
                    apathyPhilanthropistQuestResource,
                    apathyQuestResource
                );
        }

        return dominantHexad switch
        {
            "explorer" => explorerQuestResource,
            "socializer" => socializerQuestResource,
            "achiever" => achieverQuestResource,
            "disruptor" => disruptorQuestResource,
            "free_spirit" => freeSpiritQuestResource,
            "philanthropist" => philanthropistQuestResource,
            _ => string.Empty
        };
    }

    private string GetCombinedFlowQuestResource(
        string dominantHexad,
        string explorerResource,
        string socializerResource,
        string achieverResource,
        string disruptorResource,
        string freeSpiritResource,
        string philanthropistResource,
        string fallbackResource)
    {
        var mapped = dominantHexad switch
        {
            "explorer" => explorerResource,
            "socializer" => socializerResource,
            "achiever" => achieverResource,
            "disruptor" => disruptorResource,
            "free_spirit" => freeSpiritResource,
            "philanthropist" => philanthropistResource,
            _ => fallbackResource
        };

        return string.IsNullOrWhiteSpace(mapped) ? fallbackResource : mapped;
    }
}
