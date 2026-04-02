using UnityEngine;
using UnityEditor;

/// <summary>
/// Creates a default PluginConfig asset at Assets/NarrativePlugin/PluginConfig.asset
/// if one does not already exist.
/// Usage: NarrativePlugin → Create Default Config
/// </summary>
public static class CreateDefaultConfig
{
    private const string AssetPath = "Assets/NarrativePlugin/PluginConfig.asset";

    [MenuItem("NarrativePlugin/Create Default Config")]
    public static void Create()
    {
        if (AssetDatabase.LoadAssetAtPath<PluginConfig>(AssetPath) != null)
        {
            Debug.Log("[NarrativePlugin] PluginConfig already exists at " + AssetPath);
            Selection.activeObject = AssetDatabase.LoadAssetAtPath<PluginConfig>(AssetPath);
            return;
        }

        var config = ScriptableObject.CreateInstance<PluginConfig>();
        // Defaults — change backendApiUrl / backendWsUrl if backend runs on another machine
        config.backendWsUrl              = "ws://localhost:8000/ws/telemetry";
        config.backendApiUrl             = "http://localhost:8000/api";
        config.telemetryIntervalSeconds  = 5f;
        config.playerId                  = "player_001";

        AssetDatabase.CreateAsset(config, AssetPath);
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();

        Selection.activeObject = config;
        Debug.Log("[NarrativePlugin] Created PluginConfig at " + AssetPath +
                  "\nNow assign it to PlayerDataLogger and NarrativeManager in the Inspector.");
    }
}
