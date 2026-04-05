# Codex Instructions

## Commit Messages
Do not add Co-Authored-By attribution to commit messages in this repository.

---

## Project Overview

**Title:** Dynamic Narrative Personalization in Games Using AI
**Student:** Rivindu Bopage — RGU ID: 2312553 | IIT ID: 20220580
**Course:** BSc Artificial Intelligence and Data Science
**Module:** CM4609 - Individual Research Project, Robert Gordon University
**Status:** Backend + Unity plugin complete. Demo game integration scripts written — needs one-time Editor setup in Unity (see below).

This is a closed-loop Unity plugin that personalises RPG narrative in real-time using:
- Telemetry-derived Hexad player type profiling (no questionnaire)
- Flow state classification (XGBoost: FLOW / BOREDOM / ANXIETY / APATHY)
- RAG-grounded LLM narrative generation (Ollama + ChromaDB)
- PPO reinforcement learning for narrative action selection (Stable-Baselines3)

---

## Repository Structure

```
fyp-v2/
├── backend/                    # FastAPI Python backend
│   ├── main.py                 # App entrypoint — 4 routers: /ws/telemetry, /api/telemetry, /api/player-model, /api/narrative
│   ├── config.py               # Pydantic settings (Ollama URL, ChromaDB path, SQLite path, cold-start 120s)
│   ├── models/                 # Pydantic schemas
│   │   ├── telemetry.py        # TelemetryBatch — 23 behavioural signals, sent every 5s
│   │   ├── player_model.py     # PlayerModel, FlowState enum, HexadProfile
│   │   └── narrative.py        # NarrativeAction enum (8 actions), NarrativeRequest/Response
│   ├── player_modeling/
│   │   ├── feature_extractor.py   # TelemetryBatch → 11-feature vector
│   │   ├── flow_classifier.py     # XGBoost → FlowState (rule-based fallback if untrained)
│   │   ├── hexad_profiler.py      # 11-feature vector → 6D continuous Hexad scores
│   │   └── modeling_service.py    # Orchestrates the above; exposes get_player_model()
│   ├── narrative/
│   │   ├── rag_retriever.py    # ChromaDB lore retrieval (numpy cosine sim fallback)
│   │   ├── memory.py           # Episodic session memory (last N narrative events)
│   │   ├── prompt_builder.py   # Assembles final LLM prompt from player model + lore + memory
│   │   └── ollama_client.py    # HTTP client for local Ollama inference
│   ├── adaptation/
│   │   ├── rl_env.py           # Gymnasium MDP — state: (FlowState, HexadProfile), action: NarrativeAction
│   │   ├── reward.py           # Reward: +1.0 FLOW, -0.5 BOREDOM/ANXIETY, -1.0 APATHY
│   │   └── agent.py            # SB3 PPO wrapper; cold-start heuristic for first 120s
│   ├── routers/
│   │   ├── telemetry.py        # WS /ws/telemetry + POST /api/telemetry
│   │   ├── player_model.py     # GET /api/player-model/{session_id}
│   │   └── narrative.py        # POST /api/narrative
│   ├── db/
│   │   └── telemetry_store.py  # SQLite — insert TelemetryBatch, query by session
│   └── tests/                  # pytest — 8 test files covering all layers
├── unity-plugin/               # UPM package (com.research.narrative-plugin, Unity 6)
│   └── Runtime/
│       ├── PluginConfig.cs     # ScriptableObject — backendApiUrl, sessionId, intervals
│       ├── PlayerDataLogger.cs # Collects 23 signals; sends TelemetryBatch via WebSocket every 5s
│       ├── NarrativeManager.cs # Polls /api/narrative every N seconds; fires ContentInjector
│       └── ContentInjector.cs  # UnityEvents: OnNarrativeReady, OnNarrativeCleared, OnError
├── lore/                       # Game world documents fed into RAG
│   ├── world.md                # Eryndal world lore
│   ├── characters.md           # NPC backstories
│   └── quests.md               # Quest descriptions
├── evaluation/
│   ├── questionnaires/         # GEQ, miniPXI, NPS-3, interview guide (Markdown)
│   └── analysis/stats_analysis.py  # Cronbach's alpha, Mann-Whitney U, descriptives
├── data/
│   ├── telemetry.db            # SQLite (auto-created)
│   └── ppo_narrative_agent.zip # Trained PPO model weights
├── docs/
│   ├── thesis.md               # Full dissertation (~12,500 words)
│   ├── thesis.tex / thesis.docx
│   ├── interim-presentation.md # Marp slides
│   ├── logbook_20220580_2312553.docx  # Weekly logbook (24 entries, Sept 2025–Mar 2026)
│   └── plans/2026-02-27-dynamic-narrative-personalization.md
└── demo-game/                  # Unity 6 testbed project (Eryndal 2D top-down RPG)
```

---

## Running the Project

```bash
# Backend
pip install -r requirements.txt
uvicorn backend.main:app --reload          # API at http://localhost:8000

# Ollama (must be running separately)
ollama pull phi3.5
ollama serve

# Tests
pytest                                     # runs backend/tests/

# PPO training (first run only if no trained model)
python -c "from backend.adaptation.agent import NarrativeAgent; NarrativeAgent(auto_train=True)"
```

**Unity plugin import:**
1. Package Manager → + → Add package from disk → select `unity-plugin/package.json`
2. Create a `PluginConfig` asset (right-click → NarrativePlugin/Config)
3. Set `backendApiUrl = http://localhost:8000/api`
4. Wire `PlayerDataLogger`, `NarrativeManager`, `ContentInjector` to a `NarrativeSystem` GameObject

---

## Key Design Decisions

- **No questionnaire for player typing.** Hexad profile is derived entirely from the 23 telemetry signals within the session. This is the primary novelty claim.
- **Cold-start heuristic.** For the first 120 seconds of a session (`flow_cold_start_seconds` in config), the system uses a rule-based mapping (ANXIETY→PROVIDE_GUIDANCE, BOREDOM→INCREASE_URGENCY, APATHY→ADD_MYSTERY, FLOW→NO_CHANGE) before the PPO policy activates.
- **Local LLM only.** Ollama with Phi-3.5 Mini (3.8B) — no external API calls. Keeps latency manageable and removes network dependency during user study.
- **RAG uses numpy cosine similarity as fallback** if ChromaDB is unavailable. See `rag_retriever.py`.
- **8 NarrativeActions:** PROVIDE_LORE, FORESHADOW, ADD_MYSTERY, EMPHASISE_STAKES, PROVIDE_GUIDANCE, INCREASE_URGENCY, TRIGGER_FLASHBACK, NO_CHANGE.
- **Reward function:** +1.0 if FLOW, -0.5 if BOREDOM or ANXIETY, -1.0 if APATHY.

---

## Evaluation Design

- **Study design:** Between-subjects, N=50 (25 Experimental with plugin, 25 Control without)
- **Primary DV:** GEQ Flow subscale
- **Secondary DVs:** GEQ Immersion, NPS-3 (custom 3-item Narrative Personalization Scale), miniPXI
- **Qualitative:** Semi-structured interviews, Reflexive Thematic Analysis (Braun & Clarke 2022)
- **Stats:** Mann-Whitney U (non-parametric), Cronbach's alpha via `evaluation/analysis/stats_analysis.py`
- **Questionnaires:** `evaluation/questionnaires/` — all in Markdown, ready to convert

---

## Thesis

The dissertation is at `docs/thesis.md` (~12,500 words). Placeholders remain for:
- `[Candidate Name]`, `[Supervisor Name]`, `[University Name]` in the header
- Chapter 5 (Results) — awaiting user study data
- Chapter 6 (Discussion) — partially drafted

The `.tex` and `.docx` versions are kept in sync manually.

---

## What Still Needs Doing

### 1. Demo Game Integration — 2 manual steps left in Unity Editor

All C# scripts are written and live in `demo-game/Assets/NarrativePlugin/`:
- `TelemetryHooks.cs` — bridges all AnyRPG events to `PlayerDataLogger`
- `ExplorationTracker.cs` — grid-based tile exploration counter
- `NarrativeUI.cs` — TMPro HUD panel with auto-dismiss and fade
- `Editor/NarrativeSceneSetup.cs` — one-click scene setup menu item
- `Editor/CreateDefaultConfig.cs` — creates the `PluginConfig` asset

**Remaining steps (must be done in Unity Editor):**

**Step 1 — Import the plugin package**
- Open the demo-game in Unity 6
- Package Manager → + → Add package from disk → `unity-plugin/package.json`

**Step 2 — Run the setup menu items in this order:**
1. Top menu → `NarrativePlugin → Create Default Config` (creates `PluginConfig.asset`)
2. Top menu → `NarrativePlugin → Setup Scene` (creates NarrativeSystem + NarrativeCanvas in scene)
3. In the Inspector, drag `PluginConfig.asset` onto:
   - `NarrativeSystem → PlayerDataLogger → Config`
   - `NarrativeSystem → NarrativeManager → Config`
4. Save the scene

**Step 3 — Smoke test**
```bash
ollama serve          # must have phi3.5 pulled
uvicorn backend.main:app --reload
```
- Press Play → walk around → trigger a kill → check backend logs for telemetry
- Wait 120 s → narrative text should appear in the bottom HUD panel

### 2. User Study (blocked by Step 1)
- Run N=50 between-subjects study (25 Experimental, 25 Control)
- Collect GEQ, NPS-3, miniPXI responses + interview recordings

### 3. Thesis Results & Discussion
- Fill Chapter 5 (Results) with real data from `evaluation/analysis/stats_analysis.py`
- Write Chapter 6 Discussion based on results
- Replace `[Candidate Name]`, `[Supervisor Name]`, `[University Name]` placeholders in `docs/thesis.md`

### 4. Final submission
- Proofread and format `docs/thesis.md` → export to `.docx` / `.pdf`
- Logbook already complete: `docs/logbook_20220580_2312553.docx`
