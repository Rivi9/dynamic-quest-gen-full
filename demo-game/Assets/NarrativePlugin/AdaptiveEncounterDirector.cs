using System.Collections.Generic;
using AnyRPG;
using UnityEngine;

/// <summary>
/// Applies a small amount of gameplay-side adaptation on top of the narrative HUD text.
/// Intended for demo purposes: urgency/stakes actions can spawn reinforcement enemies,
/// while guidance/mystery actions update the narrative manager's quest-stage context.
/// </summary>
public class AdaptiveEncounterDirector : MonoBehaviour
{
    [SerializeField] private ContentInjector injector;
    [SerializeField] private NarrativeManager narrativeManager;
    [SerializeField] private SystemGameManager systemGameManager;

    [Header("Urgency / Stakes")]
    [SerializeField] private List<UnitSpawnNode> reinforcementSpawnNodes = new List<UnitSpawnNode>();
    [SerializeField] private float reinforcementCooldownSeconds = 30f;
    [SerializeField] private string urgencyQuestStage = "Enemy reinforcements are moving in";

    [Header("Guidance / Support")]
    [SerializeField] private List<UnitSpawnNode> supportSpawnNodes = new List<UnitSpawnNode>();
    [SerializeField] private float supportCooldownSeconds = 30f;
    [SerializeField] private string guidanceQuestStage = "Follow Varis's safer northern route";

    [Header("Mystery / Lore")]
    [SerializeField] private string mysteryQuestStage = "Investigate the strange sign near the ridge";

    private int _nextReinforcementIndex;
    private int _nextSupportIndex;
    private float _lastReinforcementTime = -999f;
    private float _lastSupportTime = -999f;

    private void Start()
    {
        if (injector == null)
            injector = FindObjectOfType<ContentInjector>();

        if (narrativeManager == null)
            narrativeManager = FindObjectOfType<NarrativeManager>();

        if (systemGameManager == null)
            systemGameManager = FindObjectOfType<SystemGameManager>();

        if (injector == null)
        {
            Debug.LogWarning("[AdaptiveEncounterDirector] ContentInjector not found; adaptive gameplay changes disabled.");
            enabled = false;
            return;
        }

        injector.OnNarrativeReceived.AddListener(HandleNarrative);
    }

    private void OnDestroy()
    {
        if (injector != null)
            injector.OnNarrativeReceived.RemoveListener(HandleNarrative);
    }

    private void HandleNarrative(NarrativeResponse response)
    {
        if (response == null)
            return;

        Debug.Log($"[AdaptiveEncounterDirector] action={response.action_taken} fallback={response.fallback} tone={response.emotional_tone}");

        switch (response.action_taken)
        {
            case "INCREASE_URGENCY":
            case "RAISE_STAKES":
                ApplyUrgency();
                break;

            case "PROVIDE_GUIDANCE":
            case "LOWER_STAKES":
                ApplyGuidance();
                break;

            case "ADD_MYSTERY":
            case "LORE_REWARD":
                UpdateQuestStage(mysteryQuestStage);
                break;
        }
    }

    private void ApplyUrgency()
    {
        UpdateQuestStage(urgencyQuestStage);

        if (Time.time - _lastReinforcementTime < reinforcementCooldownSeconds)
            return;

        if (reinforcementSpawnNodes.Count == 0)
            return;

        var node = reinforcementSpawnNodes[_nextReinforcementIndex % reinforcementSpawnNodes.Count];
        _nextReinforcementIndex++;

        if (node == null)
            return;

        node.Spawn();
        _lastReinforcementTime = Time.time;
        Debug.Log($"[AdaptiveEncounterDirector] Spawned reinforcement from {node.gameObject.name}.");
    }

    private void ApplyGuidance()
    {
        UpdateQuestStage(guidanceQuestStage);

        if (!IsCombatPressureActive())
        {
            Debug.Log("[AdaptiveEncounterDirector] Guidance received outside combat; skipping support spawn.");
            return;
        }

        if (Time.time - _lastSupportTime < supportCooldownSeconds)
            return;

        if (supportSpawnNodes.Count == 0)
            return;

        var node = supportSpawnNodes[_nextSupportIndex % supportSpawnNodes.Count];
        _nextSupportIndex++;

        if (node == null)
            return;

        node.Spawn();
        _lastSupportTime = Time.time;
        Debug.Log($"[AdaptiveEncounterDirector] Spawned support from {node.gameObject.name}.");
    }

    private bool IsCombatPressureActive()
    {
        if (systemGameManager == null)
            return false;

        var activeCharacter = systemGameManager.PlayerManager?.ActiveCharacter;
        if (activeCharacter?.CharacterCombat == null)
            return false;

        // Guidance support should only appear while the player is actively in combat.
        return activeCharacter.CharacterCombat.GetInCombat();
    }

    private void UpdateQuestStage(string nextStage)
    {
        if (narrativeManager == null || string.IsNullOrWhiteSpace(nextStage))
            return;

        narrativeManager.currentQuestStage = nextStage;
        Debug.Log($"[AdaptiveEncounterDirector] Updated quest stage context to: {nextStage}");
    }
}
