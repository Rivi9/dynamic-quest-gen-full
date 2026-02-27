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
    public string currentLocation = "Ashfen Village";
    public string currentQuestStage = "Find the broken seal";

    [Range(10f, 60f)]
    public float narrativePollingInterval = 30f;

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

    // Call this from game code to trigger an immediate narrative update (e.g., on major plot event)
    public void RequestImmediateNarrative()
    {
        StartCoroutine(FetchNarrative());
    }

    private void RequestNarrative()
    {
        StartCoroutine(FetchNarrative());
    }

    private IEnumerator FetchNarrative()
    {
        var sessionId = (logger != null) ? logger.SessionId : System.Guid.NewGuid().ToString();
        var req = new NarrativeRequest
        {
            session_id  = sessionId,
            player_id   = config.playerId,
            location    = currentLocation,
            quest_stage = currentQuestStage
        };

        var json   = JsonUtility.ToJson(req);
        var webReq = new UnityWebRequest(config.backendApiUrl + "/narrative/generate", "POST");
        webReq.uploadHandler   = new UploadHandlerRaw(Encoding.UTF8.GetBytes(json));
        webReq.downloadHandler = new DownloadHandlerBuffer();
        webReq.SetRequestHeader("Content-Type", "application/json");

        yield return webReq.SendWebRequest();

        if (webReq.result == UnityWebRequest.Result.Success)
        {
            var response = JsonUtility.FromJson<NarrativeResponse>(webReq.downloadHandler.text);
            if (response != null && !response.fallback)
                injector.Apply(response);
        }
        else
        {
            Debug.LogWarning($"[NarrativeManager] Narrative request failed: {webReq.error}");
        }

        webReq.Dispose();
    }
}
