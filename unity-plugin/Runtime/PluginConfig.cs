using UnityEngine;

[CreateAssetMenu(fileName = "PluginConfig", menuName = "NarrativePlugin/Config")]
public class PluginConfig : ScriptableObject
{
    [Header("Backend Connection")]
    public string backendWsUrl = "ws://localhost:8000/ws/telemetry";
    public string backendApiUrl = "http://localhost:8000/api";

    [Header("Telemetry Settings")]
    [Range(2f, 15f)]
    public float telemetryIntervalSeconds = 5f;

    [Header("Session")]
    public string playerId = "player_001";
}
