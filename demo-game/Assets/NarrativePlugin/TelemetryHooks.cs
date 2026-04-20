using AnyRPG;
using UnityEngine;
using UnityEngine.SceneManagement;

/// <summary>
/// Bridges AnyRPG game events to the NarrativePlugin PlayerDataLogger.
/// Drop this on the same NarrativeSystem GameObject as PlayerDataLogger.
/// No Inspector wiring needed beyond the logger reference.
/// </summary>
public class TelemetryHooks : MonoBehaviour
{
    [SerializeField] private PlayerDataLogger logger;
    [SerializeField] private NarrativeManager narrativeManager;
    [SerializeField] private NarrativeTriggerDirector triggerDirector;

    private SystemGameManager _sgm;
    private CharacterCombat   _playerCombat;
    private bool              _hooked;          // true once SGM events are subscribed
    private Dialog            _activeDialog;
    private bool              _dialogCompletedThisOpen;

    // ── Lifecycle ────────────────────────────────────────────────────────────

    private void Start()
    {
        if (logger == null)
        {
            Debug.LogError("[TelemetryHooks] PlayerDataLogger reference is not set.");
            enabled = false;
            return;
        }

        if (triggerDirector == null)
            triggerDirector = FindObjectOfType<NarrativeTriggerDirector>();

        // Subscribe to scene load so we can retry finding SGM after a scene transition
        SceneManager.sceneLoaded += OnSceneLoaded;

        TryHookSGM();
    }

    private void OnSceneLoaded(Scene scene, LoadSceneMode mode)
    {
        if (!_hooked)
            TryHookSGM();
    }

    /// <summary>
    /// Attempts to find SystemGameManager and subscribe to all AnyRPG events.
    /// Safe to call multiple times — skips if already hooked.
    /// </summary>
    private void TryHookSGM()
    {
        if (_hooked) return;

        _sgm = FindObjectOfType<SystemGameManager>();
        if (_sgm == null)
        {
            Debug.Log("[TelemetryHooks] SystemGameManager not in this scene yet — will retry on next scene load.");
            return;
        }

        // Static string-keyed events (no reference needed)
        SystemEventManager.StartListening("OnPlayerDeath",                HandlePlayerDeath);
        SystemEventManager.StartListening("OnQuestObjectiveStatusUpdated",HandleQuestObjectiveUpdated);
        SystemEventManager.StartListening("OnQuestStatusUpdated",         HandleQuestStatusUpdated);
        SystemEventManager.StartListening("OnTakeLoot",                   HandleLootTaken);
        SystemEventManager.StartListening("OnLevelLoad",                  HandleLevelLoad);
        SystemEventManager.StartListening("OnPlayerUnitSpawn",            HandlePlayerSpawned);
        SystemEventManager.StartListening("OnPlayerUnitDespawn",          HandlePlayerDespawned);
        SystemEventManager.StartListening("OnXPGained",                   HandleXPGained);

        // Instance events on SystemEventManager
        _sgm.SystemEventManager.OnTakeDamage             += HandleTakeDamage;
        _sgm.SystemEventManager.OnInteractionStarted     += HandleInteractionStarted;
        _sgm.SystemEventManager.OnDialogCompleted        += HandleDialogCompleted;
        if (_sgm.UIManager?.dialogWindow != null)
        {
            _sgm.UIManager.dialogWindow.OnOpenWindowCallback += HandleDialogWindowOpened;
            _sgm.UIManager.dialogWindow.OnCloseWindowCallback += HandleDialogWindowClosed;
        }

        _hooked = true;

        TryHookPlayerCombat();

        logger.SetLocation(SceneManager.GetActiveScene().name);
        Debug.Log("[TelemetryHooks] Hooked into SystemGameManager in scene: " +
                  SceneManager.GetActiveScene().name);
    }

    private void OnDestroy()
    {
        SceneManager.sceneLoaded -= OnSceneLoaded;

        if (_hooked)
        {
            SystemEventManager.StopListening("OnPlayerDeath",                HandlePlayerDeath);
            SystemEventManager.StopListening("OnQuestObjectiveStatusUpdated",HandleQuestObjectiveUpdated);
            SystemEventManager.StopListening("OnQuestStatusUpdated",         HandleQuestStatusUpdated);
            SystemEventManager.StopListening("OnTakeLoot",                   HandleLootTaken);
            SystemEventManager.StopListening("OnLevelLoad",                  HandleLevelLoad);
            SystemEventManager.StopListening("OnPlayerUnitSpawn",            HandlePlayerSpawned);
            SystemEventManager.StopListening("OnPlayerUnitDespawn",          HandlePlayerDespawned);
            SystemEventManager.StopListening("OnXPGained",                   HandleXPGained);

            if (_sgm != null)
            {
                _sgm.SystemEventManager.OnTakeDamage         -= HandleTakeDamage;
                _sgm.SystemEventManager.OnInteractionStarted -= HandleInteractionStarted;
                _sgm.SystemEventManager.OnDialogCompleted    -= HandleDialogCompleted;
                if (_sgm.UIManager?.dialogWindow != null)
                {
                    _sgm.UIManager.dialogWindow.OnOpenWindowCallback -= HandleDialogWindowOpened;
                    _sgm.UIManager.dialogWindow.OnCloseWindowCallback -= HandleDialogWindowClosed;
                }
            }
        }

        UnhookPlayerCombat();
    }

    // ── Player combat hook (re-acquired on each spawn) ────────────────────

    private void TryHookPlayerCombat()
    {
        if (_sgm.PlayerManager?.ActiveCharacter?.CharacterCombat == null) return;
        UnhookPlayerCombat();
        _playerCombat = _sgm.PlayerManager.ActiveCharacter.CharacterCombat;
        _playerCombat.OnKillEvent += HandleKill;
        _playerCombat.OnHitEvent += HandleHitEvent;
        _playerCombat.OnReceiveCombatMiss += HandleCombatMiss;
    }

    private void UnhookPlayerCombat()
    {
        if (_playerCombat != null)
        {
            _playerCombat.OnKillEvent -= HandleKill;
            _playerCombat.OnHitEvent -= HandleHitEvent;
            _playerCombat.OnReceiveCombatMiss -= HandleCombatMiss;
            _playerCombat = null;
        }
    }

    // ── Event handlers ────────────────────────────────────────────────────

    private void HandlePlayerSpawned(string _, EventParamProperties __)
    {
        TryHookPlayerCombat();
    }

    private void HandlePlayerDespawned(string _, EventParamProperties __)
    {
        UnhookPlayerCombat();
    }

    private void HandleKill(BaseCharacter victim, float creditPercent)
    {
        if (creditPercent > 0f)
        {
            logger.OnKill();
            triggerDirector?.TriggerCombatVictory("enemy_killed");
        }
    }

    private void HandlePlayerDeath(string _, EventParamProperties __)
    {
        logger.OnDeath();
    }

    // Damage — filter to player only (target.BaseCharacter == active player)
    private void HandleTakeDamage(IAbilityCaster source, CharacterUnit target, int damage, string abilityName)
    {
        if (_sgm?.PlayerManager?.ActiveCharacter == null) return;
        if (target?.BaseCharacter == _sgm.PlayerManager.ActiveCharacter)
        {
            logger.OnDamageTaken(damage);
            Debug.Log($"[TelemetryHooks] damage_taken += {damage} via {abilityName}");
            if (damage >= 5)
                triggerDirector?.TriggerCombatPressure("heavy_damage_taken");
        }
        else if (source?.AbilityManager?.GetCharacterUnit()?.BaseCharacter == _sgm.PlayerManager.ActiveCharacter)
        {
            logger.OnDamageDealt(damage);
            Debug.Log($"[TelemetryHooks] damage_dealt += {damage} via {abilityName}");
        }
    }

    // Quest objective ticked (e.g. kill 3/5 → 4/5)
    private void HandleQuestObjectiveUpdated(string _, EventParamProperties props)
    {
        logger.OnObjectiveAttempted();
    }

    // Quest fully completed / turned in
    private void HandleQuestStatusUpdated(string _, EventParamProperties props)
    {
        // Check if any tracked quest just became completable/complete
        if (_sgm?.QuestLog == null) return;

        // AnyRPG doesn't pass the quest name in props; use QuestLog to find the active quest
        // and update NarrativeManager's quest stage if we can determine it.
        logger.OnObjectiveCompleted();

        // Mirror into NarrativeManager so it sends updated context on next poll
        if (narrativeManager != null)
        {
            // Best-effort: set quest stage to "Quest Completed" so the LLM knows
            narrativeManager.currentQuestStage = "Quest completed";
        }

        triggerDirector?.TriggerQuestUpdate("quest_completed");
    }

    // Loot taken — treat each loot event as an item pickup
    private void HandleLootTaken(string _, EventParamProperties __)
    {
        logger.OnLoreItemFound();
        triggerDirector?.TriggerExploration("loot_or_lore_found");
    }

    // NPC / interactable interaction started
    private void HandleInteractionStarted(string interactableName)
    {
        logger.OnVoluntaryNPCInteraction();
        triggerDirector?.TriggerDialogue("interaction_started");
    }

    // Dialogue window closed (all lines shown)
    private void HandleDialogCompleted(Dialog dialog)
    {
        _dialogCompletedThisOpen = true;
        int shownLines = Mathf.Max(1, dialog != null ? dialog.DialogNodes.Count : 1);
        for (int i = 0; i < shownLines; i++)
            logger.OnDialogueShown();
        Debug.Log($"[TelemetryHooks] dialogue_lines_shown += {shownLines}");
        triggerDirector?.TriggerDialogue("dialogue_completed");
    }

    // Level/zone loaded — use scene display name as location
    private void HandleLevelLoad(string _, EventParamProperties props)
    {
        var zoneName = props?.simpleParams?.StringParam;
        if (!string.IsNullOrEmpty(zoneName))
        {
            logger.SetLocation(zoneName);
            if (narrativeManager != null)
                narrativeManager.currentLocation = zoneName;
        }
    }

    // XP gain — use as a proxy signal that an objective-style event happened
    private void HandleXPGained(string _, EventParamProperties __)
    {
        logger.OnObjectiveAttempted();
    }

    private void HandleHitEvent(BaseCharacter attacker, Interactable target)
    {
        if (_sgm?.PlayerManager?.ActiveCharacter == null) return;
        if (attacker == _sgm.PlayerManager.ActiveCharacter)
        {
            logger.OnAbilityUsed(true);
            Debug.Log("[TelemetryHooks] abilities_used += 1, abilities_hit += 1");
        }
    }

    private void HandleCombatMiss(Interactable target, AbilityEffectContext abilityEffectContext)
    {
        logger.OnAbilityUsed(false);
        Debug.Log("[TelemetryHooks] abilities_used += 1, abilities_hit += 0 (miss)");
    }

    private void HandleDialogWindowOpened()
    {
        _activeDialog = _sgm?.DialogManager?.Dialog;
        _dialogCompletedThisOpen = false;
    }

    private void HandleDialogWindowClosed()
    {
        if (_dialogCompletedThisOpen || _activeDialog == null)
        {
            _activeDialog = null;
            return;
        }

        int skippedLines = 0;
        foreach (DialogNode node in _activeDialog.DialogNodes)
        {
            if (node != null && !node.Shown)
                skippedLines++;
        }

        if (skippedLines <= 0 && _activeDialog.DialogNodes.Count > 0)
            skippedLines = 1;

        for (int i = 0; i < skippedLines; i++)
            logger.OnDialogueSkipped();

        Debug.Log($"[TelemetryHooks] dialogue_lines_skipped += {skippedLines}");
        triggerDirector?.TriggerDialogue("dialogue_skipped");

        _activeDialog = null;
    }
}
