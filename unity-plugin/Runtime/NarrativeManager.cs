using System.Collections;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

[System.Serializable]
public class NarrativeRequest
{
    public string session_id;
    public string player_id;
    public string location;
    public string quest_stage;
    public string trigger_type;
    public string trigger_reason;
    public string importance;
}

[System.Serializable]
public class NarrativeResponse
{
    public string action_taken;
    public string content_type;
    public string content;
    public string speaker;
    public string emotional_tone;
    public bool fallback;
}

public class NarrativeManager : MonoBehaviour
{
    [SerializeField] private PluginConfig config;
    [SerializeField] private ContentInjector injector;
    [SerializeField] private PlayerDataLogger logger;

    [Header("Context (update from game systems)")]
    public string currentLocation = "FeaturesDemoZone";
    public string currentQuestStage = "Patrol the Contested Vale";

    [Range(10f, 60f)]
    public float narrativePollingInterval = 30f;

    [Header("Request Gating")]
    [Range(0f, 30f)]
    public float minimumSecondsBetweenRequests = 10f;

    private bool _requestInFlight;
    private float _lastRequestStartTime = -999f;

    private void Start()
    {
        if (config == null)
        {
            Debug.LogError("[NarrativeManager] PluginConfig is not assigned. Disabling component.");
            enabled = false;
            return;
        }

        if (injector == null)
        {
            Debug.LogError("[NarrativeManager] ContentInjector is not assigned. Disabling component.");
            enabled = false;
            return;
        }

        InvokeRepeating(nameof(RequestNarrative), narrativePollingInterval, narrativePollingInterval);
    }

    private void OnDestroy()
    {
        CancelInvoke(nameof(RequestNarrative));
        StopAllCoroutines();
    }

    public void RequestImmediateNarrative()
    {
        RequestImmediateNarrative("event", "manual_request", "medium");
    }

    public void RequestImmediateNarrative(string triggerType, string triggerReason, string importance = "medium")
    {
        if (_requestInFlight)
        {
            Debug.Log($"[NarrativeManager] Skipping immediate narrative request while another is in flight ({triggerType}/{triggerReason}).");
            return;
        }

        if (!CanStartRequest(triggerType, triggerReason))
            return;

        StartCoroutine(FetchNarrative(triggerType, triggerReason, importance));
    }

    private void RequestNarrative()
    {
        if (!CanStartRequest("poll", "interval"))
            return;

        Debug.Log($"[NarrativeManager] Polling narrative - location: {currentLocation}, quest: {currentQuestStage}");
        StartCoroutine(FetchNarrative("poll", "interval", "low"));
    }

    private IEnumerator FetchNarrative(string triggerType, string triggerReason, string importance)
    {
        _requestInFlight = true;
        _lastRequestStartTime = Time.time;

        var sessionId = (logger != null) ? logger.SessionId : System.Guid.NewGuid().ToString();
        var req = new NarrativeRequest
        {
            session_id = sessionId,
            player_id = config.playerId,
            location = currentLocation,
            quest_stage = currentQuestStage,
            trigger_type = string.IsNullOrWhiteSpace(triggerType) ? "poll" : triggerType,
            trigger_reason = string.IsNullOrWhiteSpace(triggerReason) ? "interval" : triggerReason,
            importance = string.IsNullOrWhiteSpace(importance) ? "low" : importance
        };

        var json = JsonUtility.ToJson(req);
        var webReq = new UnityWebRequest(config.backendApiUrl + "/narrative/generate", "POST");
        webReq.uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes(json));
        webReq.downloadHandler = new DownloadHandlerBuffer();
        webReq.SetRequestHeader("Content-Type", "application/json");

        yield return webReq.SendWebRequest();

        if (webReq.result == UnityWebRequest.Result.Success)
        {
            Debug.Log($"[NarrativeManager] Response: {webReq.downloadHandler.text}");
            var response = JsonUtility.FromJson<NarrativeResponse>(webReq.downloadHandler.text);
            if (response != null)
                injector.Apply(response);
            else
                Debug.LogWarning("[NarrativeManager] Response parsed as null.");
        }
        else
        {
            Debug.LogWarning($"[NarrativeManager] Request failed: {webReq.error} - URL: {config.backendApiUrl}/narrative/generate");
        }

        webReq.Dispose();
        _requestInFlight = false;
    }

    private bool CanStartRequest(string triggerType, string triggerReason)
    {
        if (Time.time - _lastRequestStartTime < minimumSecondsBetweenRequests)
        {
            Debug.Log($"[NarrativeManager] Skipping {triggerType}/{triggerReason} - minimum request gap not reached.");
            return false;
        }

        return true;
    }
}
