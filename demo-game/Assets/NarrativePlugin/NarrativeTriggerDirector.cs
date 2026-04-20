using AnyRPG;
using UnityEngine;

/// <summary>
/// Sends immediate narrative requests for meaningful gameplay moments so the plugin
/// reacts closer to the situation that caused the telemetry change.
/// </summary>
public class NarrativeTriggerDirector : MonoBehaviour
{
    [SerializeField] private NarrativeManager narrativeManager;
    [SerializeField] private SystemGameManager systemGameManager;

    [Header("Cooldowns")]
    [SerializeField] private float combatPressureCooldownSeconds = 20f;
    [SerializeField] private float combatVictoryCooldownSeconds = 20f;
    [SerializeField] private float dialogueCooldownSeconds = 20f;
    [SerializeField] private float explorationCooldownSeconds = 30f;
    [SerializeField] private float questCooldownSeconds = 15f;
    [SerializeField] private float idleCooldownSeconds = 60f;

    [Header("Idle Detection")]
    [SerializeField] private float idleThresholdSeconds = 25f;
    [SerializeField] private float movementThreshold = 0.2f;

    private float _lastCombatPressureTime = -999f;
    private float _lastCombatVictoryTime = -999f;
    private float _lastDialogueTime = -999f;
    private float _lastExplorationTime = -999f;
    private float _lastQuestTime = -999f;
    private float _lastIdleTime = -999f;
    private float _lastMovementTime;
    private Vector3 _lastKnownPlayerPosition;
    private bool _hasPlayerPosition;

    private void Start()
    {
        if (narrativeManager == null)
            narrativeManager = FindObjectOfType<NarrativeManager>();

        if (systemGameManager == null)
            systemGameManager = FindObjectOfType<SystemGameManager>();

        _lastMovementTime = Time.time;
    }

    private void Update()
    {
        var activeCharacter = systemGameManager?.PlayerManager?.ActiveCharacter;
        if (activeCharacter == null)
            return;

        var currentPosition = activeCharacter.transform.position;
        if (!_hasPlayerPosition)
        {
            _lastKnownPlayerPosition = currentPosition;
            _hasPlayerPosition = true;
            return;
        }

        if (Vector3.Distance(currentPosition, _lastKnownPlayerPosition) > movementThreshold)
        {
            _lastKnownPlayerPosition = currentPosition;
            _lastMovementTime = Time.time;
        }

        if (activeCharacter.CharacterCombat?.GetInCombat() == true)
            return;

        if (Time.time - _lastMovementTime < idleThresholdSeconds)
            return;

        if (Time.time - _lastIdleTime < idleCooldownSeconds)
            return;

        _lastIdleTime = Time.time;
        SendTrigger("idle", "idle_threshold_reached", "medium");
    }

    public void TriggerCombatPressure(string reason)
    {
        if (Time.time - _lastCombatPressureTime < combatPressureCooldownSeconds)
            return;

        _lastCombatPressureTime = Time.time;
        SendTrigger("combat", reason, "high");
    }

    public void TriggerCombatVictory(string reason)
    {
        if (Time.time - _lastCombatVictoryTime < combatVictoryCooldownSeconds)
            return;

        _lastCombatVictoryTime = Time.time;
        SendTrigger("combat", reason, "medium");
    }

    public void TriggerDialogue(string reason)
    {
        if (Time.time - _lastDialogueTime < dialogueCooldownSeconds)
            return;

        _lastDialogueTime = Time.time;
        SendTrigger("dialogue", reason, "medium");
    }

    public void TriggerExploration(string reason)
    {
        if (Time.time - _lastExplorationTime < explorationCooldownSeconds)
            return;

        _lastExplorationTime = Time.time;
        SendTrigger("exploration", reason, "medium");
    }

    public void TriggerQuestUpdate(string reason)
    {
        if (Time.time - _lastQuestTime < questCooldownSeconds)
            return;

        _lastQuestTime = Time.time;
        SendTrigger("quest", reason, "high");
    }

    private void SendTrigger(string triggerType, string triggerReason, string importance)
    {
        if (narrativeManager == null)
            return;

        Debug.Log($"[NarrativeTriggerDirector] Triggering narrative: {triggerType}/{triggerReason} ({importance})");
        narrativeManager.RequestImmediateNarrative(triggerType, triggerReason, importance);
    }
}
