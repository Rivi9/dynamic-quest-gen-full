# Demo Setup & Next Steps

**Project:** Dynamic Narrative Personalization in Games Using AI
**Student:** Rivindu Bopage — RGU 2312553 / IIT 20220580

---

## 1. Prerequisites

Before opening Unity, start the backend services:

```bash
# Terminal 1 — Ollama (must be running before the backend)
ollama serve
# (phi3.5 must already be pulled: ollama pull phi3.5)

# Terminal 2 — FastAPI backend
cd e:/Projects/fyp/v2
uvicorn backend.main:app --reload
# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

Verify the backend is up:
```bash
curl http://localhost:8000/api/player-model/test-session
```

---

## 2. Unity Setup (one-time, already scripted)

Open `demo-game/` in **Unity 6**.

### Step 1 — Package is already registered
`manifest.json` already has:
```json
"com.research.narrative-plugin": "file:../../unity-plugin"
```
Unity should resolve this automatically on open. If you see errors, go to **Edit → Project Settings → Package Manager** and click **Reset Packages to defaults**, then re-add.

### Step 2 — Create the PluginConfig asset
Top menu → **NarrativePlugin → Create Default Config**

This creates `Assets/NarrativePlugin/PluginConfig.asset` with:
- WebSocket URL: `ws://localhost:8000/ws/telemetry`
- API URL: `http://localhost:8000/api`
- Telemetry interval: 5 s

### Step 3 — Set up the scene
Open the scene `Assets/AnyRPG/Core/Games/FeaturesDemoGame/Scenes/FeaturesDemoScene.unity`.

Top menu → **NarrativePlugin → Setup Scene**

This creates two GameObjects in the hierarchy:
- `NarrativeSystem` — PlayerDataLogger, NarrativeManager, ContentInjector, TelemetryHooks, ExplorationTracker
- `NarrativeCanvas` — HUD panel wired to ContentInjector events

### Step 4 — Assign the config
In the Inspector, drag `PluginConfig.asset` onto:
- `NarrativeSystem → PlayerDataLogger → Config`
- `NarrativeSystem → NarrativeManager → Config`

### Step 5 — Save the scene
**File → Save** (Ctrl+S). The scene must be saved or the wiring is lost on next open.

---

## 3. Smoke Test

Press **Play** in Unity.

**What to verify in order:**

| Check | How | Expected |
|---|---|---|
| WebSocket connects | Backend terminal | `WebSocket connected: <session_id>` log line |
| Telemetry arrives | Backend terminal | JSON batches logged every 5 s |
| No console errors | Unity Console | No red errors from NarrativePlugin scripts |
| Kill event fires | Kill any enemy, watch Console | `[TelemetryHooks]` log or kill count increments |
| Zone name correct | Backend logs after load | `location: "The Contested Vale"` (not `"FeaturesDemoZone"`) |
| Narrative fires | Wait 30 s (default poll) | HUD panel appears at bottom of screen with narrative text |

If the HUD panel never appears after 30 s, check:
1. Backend logs — did `/api/narrative/generate` receive a request?
2. Is Ollama serving? (`ollama ps` — phi3.5 should be listed)
3. Is `fallback: true` in the response? (means LLM failed, check Ollama)

---

## 4. Control vs Experimental Build

For the user study you need two builds from the same scene:

| Build | What changes | How |
|---|---|---|
| **Experimental** | Plugin active (default) | Leave NarrativeSystem enabled |
| **Control** | Plugin disabled | In the scene, uncheck `NarrativeSystem` GameObject before building |

Build via **File → Build Settings → Build**. Use a different output folder for each.

---

## 5. Next Steps — Implementation

### 5.1 Verify TelemetryHooks event wiring (HIGH PRIORITY)
The hooks use AnyRPG's `SystemEventManager`. Some event names may differ between AnyRPG versions.

Check each event string against `Assets/AnyRPG/Core/System/Scripts/GameManager/SystemEventManager.cs`:
- `"OnPlayerDeath"`
- `"OnQuestObjectiveStatusUpdated"`
- `"OnQuestStatusUpdated"`
- `"OnTakeLoot"`
- `"OnLevelLoad"`
- `"OnPlayerUnitSpawn"` / `"OnPlayerUnitDespawn"`
- `"OnXPGained"`

If any are wrong, fix them in [TelemetryHooks.cs](../demo-game/Assets/NarrativePlugin/TelemetryHooks.cs).

### 5.2 Verify instance event signatures
`_sgm.SystemEventManager.OnTakeDamage`, `.OnInteractionStarted`, `.OnDialogCompleted` — confirm their delegate signatures match what's in AnyRPG. If the build fails on these lines, look up the correct signature in `SystemEventManager.cs` and update `TelemetryHooks.cs`.

### 5.3 Quest stage tracking (LOW effort, HIGH narrative quality)
Currently `NarrativeManager.currentQuestStage` is only updated to `"Quest completed"` on any quest change. A better approach: set it to the active quest's display name.

In [TelemetryHooks.cs:147](../demo-game/Assets/NarrativePlugin/TelemetryHooks.cs#L147), replace the hardcoded string with a lookup from `_sgm.QuestLog` to get the active quest name.

### 5.4 Narrative polling interval
Default is 30 s (set in `NarrativeManager.narrativePollingInterval`). For the demo/study:
- **30 s** is fine for a 20-minute session (generates ~40 narratives)
- Reduce to **20 s** if testers feel nothing is happening
- Increase to **60 s** if Ollama is slow on the study machine

Adjust in the Inspector on `NarrativeSystem → NarrativeManager`.

### 5.5 RAG lore ingestion (MUST DO before study)
The lore files are written but not yet loaded into ChromaDB. On first backend start, run:

```bash
cd e:/Projects/fyp/v2
python -c "
from backend.narrative.rag_retriever import RAGRetriever
r = RAGRetriever()
r.ingest_directory('lore/')
print('Lore ingested.')
"
```

Verify with a test query:
```bash
python -c "
from backend.narrative.rag_retriever import RAGRetriever
r = RAGRetriever()
print(r.retrieve('The Contested Vale', n=2))
"
```
Expected: returns world.md text about FeaturesDemoZone.

### 5.6 PPO agent training (MUST DO before study)
If `data/ppo_narrative_agent.zip` does not exist or is stale, train it:

```bash
python -c "from backend.adaptation.agent import NarrativeAgent; NarrativeAgent(auto_train=True)"
```

This takes a few minutes. The trained model is saved automatically.

---

## 6. Next Steps — User Study

### 6.1 Prepare two machines (or two Unity builds)
- Experimental build: NarrativeSystem active
- Control build: NarrativeSystem disabled

Both builds must connect to the same backend if running in parallel, or run separate backend instances with separate SQLite databases.

### 6.2 Participant flow
1. Consent form → demographics
2. 5-minute orientation (show controls, explain the world)
3. 20-minute play session
4. GEQ questionnaire (`evaluation/questionnaires/GEQ.md`)
5. NPS-3 questionnaire (`evaluation/questionnaires/NPS3.md`)
6. miniPXI questionnaire (`evaluation/questionnaires/miniPXI.md`)
7. 10-minute semi-structured interview (`evaluation/questionnaires/interview_guide.md`)

Target: N=50 (25 Experimental, 25 Control). Aim to run both conditions in parallel to control for time-of-day effects.

### 6.3 Data collection
Telemetry is stored automatically in `data/telemetry.db`. After each session:
```bash
# Export session summary
curl http://localhost:8000/api/player-model/<session_id>
```

Questionnaire responses: collect on paper or Google Forms, then enter into a CSV matching `session_id`.

### 6.4 Analysis
```bash
python evaluation/analysis/stats_analysis.py
```

This computes Cronbach's alpha per scale and Mann-Whitney U between conditions. Fill the CSV path in the script before running.

---

## 7. Next Steps — Thesis

| Section | Status | Action |
|---|---|---|
| Ch 1–4 (Background, Method) | Complete | Proofread only |
| Ch 5 Results | Empty | Run stats after study, paste output |
| Ch 6 Discussion | Partial draft | Write after results |
| Header placeholders | `[Candidate Name]` etc. | Replace with actual names |
| References | Mostly complete | Check any added since last edit |

Export pipeline: `docs/thesis.md` → Pandoc → `.docx` → submit.

---

## 8. Known Issues / Watch Points

- **`FindObjectOfType<SystemGameManager>()`** — works at runtime but is slow. Not a problem for a research prototype.
- **`_sgm.SystemEventManager.OnInteractionStarted`** signature — takes `string interactableName`. If AnyRPG's version takes a different type, `TelemetryHooks.cs:162` will fail to compile.
- **`ContentInjector` UnityEvent wiring** — wired programmatically in `NarrativeSceneSetup.cs`. If the events don't fire, open `NarrativeSystem → ContentInjector` in the Inspector and confirm the listeners are listed under `OnDialogueInjected`, `OnDescriptionInjected`, `OnQuestUpdateInjected`.
- **Ollama cold start** — first inference after `ollama serve` takes ~10 s. Subsequent calls are fast. Warn study participants there may be a brief delay on the first narrative.
- **Single-session PPO** — the RL agent accumulates experience across sessions in the same process. Restarting the backend resets the in-memory PPO buffer (model weights on disk are preserved).
