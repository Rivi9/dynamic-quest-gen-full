using System;
using System.Collections;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

[Serializable]
public class TelemetryBatch
{
    public string player_id;
    public string session_id;
    public double window_start;
    public double window_end;
    public int kills;
    public int deaths;
    public float damage_taken;
    public float damage_dealt;
    public int abilities_used;
    public int abilities_hit;
    public int objectives_completed;
    public int objectives_attempted;
    public int tiles_explored;
    public int total_tiles = 100;
    public int npc_interactions_voluntary;
    public int dialogue_lines_shown;
    public int dialogue_lines_skipped;
    public int lore_items_read;
    public int lore_items_found;
    public float idle_seconds;
    public float session_elapsed;
    public string current_location = "unknown";
    public string current_objective = "none";
}

public class PlayerDataLogger : MonoBehaviour
{
    [SerializeField] private PluginConfig config;

    private TelemetryBatch _currentBatch;
    private string _sessionId;
    private float _windowStart;
    private float _sessionStart;
    private float _lastMoveTime;

    // Public API — call these from your game systems
    public void OnKill()                        => _currentBatch.kills++;
    public void OnDeath()                       => _currentBatch.deaths++;
    public void OnDamageTaken(float amt)        => _currentBatch.damage_taken += amt;
    public void OnDamageDealt(float amt)        => _currentBatch.damage_dealt += amt;
    public void OnAbilityUsed(bool hit)         { _currentBatch.abilities_used++; if (hit) _currentBatch.abilities_hit++; }
    public void OnObjectiveAttempted()          => _currentBatch.objectives_attempted++;
    public void OnObjectiveCompleted()          => _currentBatch.objectives_completed++;
    public void OnTileExplored(int totalCount)  => _currentBatch.tiles_explored = totalCount;
    public void OnVoluntaryNPCInteraction()     => _currentBatch.npc_interactions_voluntary++;
    public void OnDialogueShown()               => _currentBatch.dialogue_lines_shown++;
    public void OnDialogueSkipped()             => _currentBatch.dialogue_lines_skipped++;
    public void OnLoreItemFound()               => _currentBatch.lore_items_found++;
    public void OnLoreItemRead()                => _currentBatch.lore_items_read++;
    public void OnPlayerMoved()                 => _lastMoveTime = Time.time;

    public void SetLocation(string location)    => _currentBatch.current_location = location;
    public void SetObjective(string objective)  => _currentBatch.current_objective = objective;

    public string SessionId => _sessionId;

    private void Awake()
    {
        _sessionId  = Guid.NewGuid().ToString();
        _sessionStart = Time.time;
        _lastMoveTime = Time.time;
        StartNewBatch();
        InvokeRepeating(nameof(SendBatch), config.telemetryIntervalSeconds,
                        config.telemetryIntervalSeconds);
    }

    private void Update()
    {
        // Accumulate idle time when player hasn't moved for > 2 seconds
        if (Time.time - _lastMoveTime > 2f)
            _currentBatch.idle_seconds += Time.deltaTime;
    }

    private void StartNewBatch()
    {
        _windowStart  = Time.time;
        _currentBatch = new TelemetryBatch
        {
            player_id  = config.playerId,
            session_id = _sessionId,
            window_start = _windowStart,
            total_tiles  = 100,
        };
    }

    private void SendBatch()
    {
        _currentBatch.window_end      = Time.time;
        _currentBatch.session_elapsed = Time.time - _sessionStart;
        var json = JsonUtility.ToJson(_currentBatch);
        StartCoroutine(PostTelemetry(json));
        StartNewBatch();
    }

    private IEnumerator PostTelemetry(string json)
    {
        var url = config.backendApiUrl + "/telemetry";
        var req = new UnityWebRequest(url, "POST");
        req.uploadHandler   = new UploadHandlerRaw(Encoding.UTF8.GetBytes(json));
        req.downloadHandler = new DownloadHandlerBuffer();
        req.SetRequestHeader("Content-Type", "application/json");
        yield return req.SendWebRequest();

        if (req.result != UnityWebRequest.Result.Success)
            Debug.LogWarning($"[PlayerDataLogger] Telemetry POST failed: {req.error}");
    }
}
