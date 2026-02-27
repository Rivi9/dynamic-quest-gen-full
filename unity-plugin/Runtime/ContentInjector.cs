using UnityEngine;
using UnityEngine.Events;

public class ContentInjector : MonoBehaviour
{
    [Header("Events — wire these to your game UI systems in the Inspector")]
    public UnityEvent<string, string> OnDialogueInjected;   // (speaker, text)
    public UnityEvent<string>         OnDescriptionInjected; // (text)
    public UnityEvent<string>         OnQuestUpdateInjected; // (text)

    // Raised for every successful injection regardless of type — useful for logging
    public UnityEvent<NarrativeResponse> OnNarrativeReceived;

    public void Apply(NarrativeResponse response)
    {
        if (response == null || string.IsNullOrEmpty(response.content))
            return;

        OnNarrativeReceived?.Invoke(response);

        switch (response.content_type)
        {
            case "dialogue":
                var speaker = string.IsNullOrEmpty(response.speaker) ? "NPC" : response.speaker;
                OnDialogueInjected?.Invoke(speaker, response.content);
                break;
            case "description":
                OnDescriptionInjected?.Invoke(response.content);
                break;
            case "quest_update":
                OnQuestUpdateInjected?.Invoke(response.content);
                break;
            default:
                Debug.LogWarning($"[ContentInjector] Unknown content_type: {response.content_type}");
                break;
        }
    }
}
