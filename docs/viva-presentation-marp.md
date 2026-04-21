---
marp: true
theme: default
paginate: true
backgroundColor: #ffffff
style: |
  section {
    font-family: 'Segoe UI', sans-serif;
    font-size: 26px;
  }
  h1 { color: #1a1a2e; border-bottom: 3px solid #c8a951; padding-bottom: 10px; }
  h2 { color: #16213e; }
  h3 { color: #c8a951; }
  table { font-size: 20px; width: 100%; }
  th { background: #1a1a2e; color: #c8a951; }
  td { font-size: 19px; }
  code { background: #f0f4f8; border-radius: 4px; padding: 2px 6px; font-size: 20px; }
  pre { background: #1a1a2e; color: #e0e0e0; border-radius: 8px; font-size: 16px; }
  .columns { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; }
  .highlight { background: #f5f0e0; border-left: 4px solid #c8a951; padding: 12px; border-radius: 4px; font-size: 22px; }
  .stat { font-size: 42px; font-weight: bold; color: #1a1a2e; }
  .label { font-size: 16px; color: #666; }
  .rq { background: #f0f4f8; border-left: 4px solid #1a1a2e; padding: 8px 12px; margin: 6px 0; border-radius: 2px; font-size: 22px; }
  .finding { background: #e8f5e9; border-left: 4px solid #27ae60; padding: 10px; border-radius: 4px; font-size: 21px; margin: 6px 0; }
  .limitation { background: #fff3e0; border-left: 4px solid #e67e22; padding: 10px; border-radius: 4px; font-size: 21px; margin: 6px 0; }
  .kpi { text-align: center; padding: 8px; }
  .kpi .stat { display: block; }
  .kpi .label { display: block; margin-top: 4px; }
---

<!-- Slide 1: Title -->

# Dynamic Narrative Personalization in Games Using AI

**BSc (Hons) Artificial Intelligence and Data Science**
CM4609 — Individual Research Project

**Rivindu Bopage**
RGU ID: 2312553 &ensp;|&ensp; IIT ID: 20220580

Supervisor: Ms. Bimali Wickramasinghe
Informatics Institute of Technology, in collaboration with Robert Gordon University

---

<!-- Slide 2: The Problem (~2 min) -->

# The Problem

Current game narrative systems are **static**: they do not adapt their tone, urgency, or content to the psychological state and demonstrated preferences of an individual player in real time.

<div class="columns">
<div>

### What the player gets

- The same village elder warning regardless of playstyle
- The same quest text whether exploring or rushing
- No narrative response to struggle, boredom, or curiosity

</div>
<div>

### What the player needs

- A story that notices when challenge exceeds skill
- Narrative tone that matches gameplay intensity
- Content that responds to *how* they play, not just *what* they choose

</div>
</div>

<div class="highlight">

**The cost**: reduced engagement in the short term; a missed opportunity to use narrative as a lever for nudging players toward optimal experience.

</div>

---

<!-- Slide 3: Literature & Research Gap (~2 min) -->

# Literature and Research Gap

Prior work clusters into three categories, and each leaves a gap:

| Approach | Example | What's missing |
|---|---|---|
| **Authored branching** | Baldur's Gate 3, Disco Elysium | Responds to explicit choices, not behavioural signals |
| **Procedural generation** | Tracery, Expressionist | No player model; no psychological sensing |
| **LLM-based narrative** | PANGeA (AAAI 2024) | Static prompts; no RL adaptation; no episodic memory |

Six research domains converge in this work:
**Player Modelling** (Hexad) + **Flow Theory** (Csikszentmihalyi) + **RL Adaptation** (PPO) + **Narrative Personalization** + **LLMs for Games** (RAG) + **Episodic Memory** (EM-LLM)

<div class="highlight">

**The gap is integration, not invention.** Each technique exists in isolation. No prior work has wired them into a single closed loop.

</div>

---

<!-- Slide 4: Research Questions & Objectives (~1.5 min) -->

# Research Questions

<div class="rq">

**RQ1**: Can a closed-loop AI system driven by continuous Hexad profiling and Flow-state detection produce narrative that players perceive as **more personalized** than static narrative?

</div>

<div class="rq">

**RQ2**: Does PPO-driven narrative adaptation lead to measurably **higher Flow experience** (GEQ Flow subscale) compared with a control condition?

</div>

<div class="rq">

**RQ3**: How do players **perceive and experience** dynamically personalized narrative in terms of engagement and immersion?

</div>

### Study design
Between-subjects, N = 50, Welch's *t*-test, Bonferroni correction (α_adj = .0167)

---

<!-- Slide 5: System Architecture (~2 min) -->

# System Architecture: Five-Module Closed Loop

The pipeline cycles every **5 seconds** from player behaviour back to in-game delivery:

```
Player → [M1] Telemetry → [M2] Player Model → [M3] PPO Action → [M4] LLM Narrative → [M5] In-Game → Player
         (23 signals)     (Hexad + Flow)      (8 actions)       (RAG + Memory)        (HUD text)
```

| Module | Key Component | Technology |
|---|---|---|
| **M1** Telemetry | `PlayerDataLogger` | Unity C#, WebSocket, 5s windows |
| **M2** Player Model | `FeatureExtractor` → `HexadProfiler` → `FlowClassifier` | Python, rule-based decision tree |
| **M3** Adaptation | `NarrativeAgent` (PPO) | Stable-Baselines3, Gymnasium MDP |
| **M4** Generation | `LoreRetriever` → `EpisodicMemory` → `PromptBuilder` → `OllamaClient` | sentence-transformers, Ollama |
| **M5** Injection | `NarrativeManager` → `ContentInjector` | Unity C#, UnityEvents |

**Platform split**: Unity client (M1 + M5) ←→ FastAPI backend (M2 + M3 + M4)

---

<!-- Slide 6: Player Modelling (~2 min) -->

# Player Modelling: Hexad + Flow

<div class="columns">
<div>

### Hexad from Telemetry (no questionnaire)

23 raw signals → **11 features** → **6 continuous Hexad scores**

| Dimension | Behavioural Proxies |
|---|---|
| Achiever | Objective rate, KD ratio |
| Explorer | Map coverage, lore engagement |
| Socialiser | Voluntary NPC talks, dialogue |
| Free Spirit | Exploration off critical path |
| Disruptor | Kills, deaths, damage dealt |
| Philanthropist | Dialogue + lore engagement |

**Primary novelty claim**: first system to derive Hexad profiles entirely from behavioural telemetry, enabling within-session updating.

</div>
<div>

### Flow Classification

Rule-based decision tree on **challenge-skill ratio**:

```
challenge = 0.50·dmg + 0.30·(1-obj) + 0.20·deaths
skill    = 0.35·kd + 0.30·obj + 0.20·acc + 0.15·(1-idle)
ratio    = challenge / skill
```

| State | Condition |
|---|---|
| **APATHY** | idle > 0.40 AND dial < 0.30 AND ratio < 0.60 |
| **BOREDOM** | ratio < 0.75 |
| **ANXIETY** | ratio > 1.30 |
| **FLOW** | 0.75 ≤ ratio ≤ 1.30 |

Window: last 6 batches (~30s) for Flow; full session for Hexad

</div>
</div>

---

<!-- Slide 7: RL Adaptation Engine (~1.5 min) -->

# RL-Based Adaptation: PPO for Narrative

### MDP formulation

- **State**: (FlowState, HexadProfile) = 4 discrete × 6 continuous dimensions
- **Actions**: 8 narrative modulations:

<div class="columns">
<div>

| Action | Purpose |
|---|---|
| RAISE_STAKES | Increase tension |
| LOWER_STAKES | Reduce pressure |
| ADD_MYSTERY | Spark curiosity |
| ADD_HUMOR | Lighten tone |

</div>
<div>

| Action | Purpose |
|---|---|
| PROVIDE_GUIDANCE | Help struggling players |
| INCREASE_URGENCY | Accelerate pace |
| LORE_REWARD | Reward explorers |
| NO_CHANGE | Maintain current |

</div>
</div>

### Flow-based reward function (graduated penalties)

| FLOW | BOREDOM | ANXIETY | APATHY |
|---|---|---|---|
| **+1.0** | -0.3 | -0.5 | **-0.8** |

Plus: streak bonus (+0.2), transition bonus (+0.3), step penalty (-0.05), repetition penalty (-0.15)

**Cold-start heuristic**: rule-based fallback for first 120 seconds (e.g., ANXIETY → PROVIDE_GUIDANCE)

---

<!-- Slide 8: Narrative Generation (~1.5 min) -->

# Narrative Generation: RAG + Episodic Memory

<div class="columns">
<div>

### RAG pipeline

- **Lore corpus**: ~30 paragraphs (world, characters, quests)
- **Embedding**: all-MiniLM-L6-v2 (384-dim, L2-normalised)
- **Retrieval**: in-memory numpy cosine similarity; top-3 chunks
- **Dynamic**: same location + different Flow state = different lore retrieved

### LLM

- **Phi-3.5 Mini** (3.8B params) via Ollama
- Runs entirely locally: no cloud, no API keys
- JSON-mode output with structured schema
- 2-4 sentences per generation

</div>
<div>

### Episodic session memory

Inspired by EM-LLM (Fountas et al., 2024):

- **Importance-weighted** events (score 0-1)
- Capped at 10 events; evicts lowest importance
- Top 5 by importance injected into prompt
- Enables cross-event references and character continuity

### Prompt structure

```
SYSTEM: Role + tone (from Flow state)
        + output constraints
USER:   Player state + Hexad profile
        + RAG lore context (3 passages)
        + Memory context (5 events)
        + Action directive
```

**First application of episodic memory compression to real-time game narrative.**

</div>
</div>

---

<!-- Slide 9: Implementation & Demo (~2 min) -->

# Implementation

<div class="columns">
<div>

### Backend (Python)

- **FastAPI** with 4 routers: telemetry (WS + HTTP), player-model, narrative
- **SQLite** for telemetry persistence
- **Stable-Baselines3** PPO with Gymnasium MDP env
- **sentence-transformers** for RAG embeddings
- **Ollama HTTP client** for local LLM inference
- **8 test files** (pytest) covering all layers

</div>
<div>

### Unity Plugin (C# / Unity 6)

- UPM package: `com.research.narrative-plugin`
- `PlayerDataLogger`: 23 signals every 5s via WebSocket
- `NarrativeManager`: polls `/api/narrative`
- `ContentInjector`: fires `OnNarrativeReady` UnityEvent
- **Testbed**: 3D RPG on AnyRPG Core (Eryndal world)
- TMPro HUD panel with auto-dismiss and fade

</div>
</div>

### The closed loop in action

```
[Explorer behaviour: explore_rate=0.82, lore_engage=0.74]
  → Hexad: Explorer=0.82  → Flow: FLOW (ratio=1.05, confidence=0.91)
  → PPO selects: LORE_REWARD  → RAG retrieves: Eryndal ruins lore
  → LLM generates: "The ancient glyphs along the corridor walls shimmer..."
  → HUD displays narrative → Player reads (tracked) → Next telemetry cycle
```

---

<!-- Slide 10: Evaluation Design (~1.5 min) -->

# Evaluation Design

<div class="columns">
<div>

### Between-subjects experiment

- **N = 50** (25 Experimental, 25 Control)
- **30-minute** single session per participant
- **Experimental**: full 5-module adaptive system
- **Control**: same game, same triggers, static `ScriptableObject` narrative
- Everything else identical: environment, objectives, NPCs, UI, session length

### Instruments

| Scale | What it measures |
|---|---|
| **GEQ Flow** (α = .79) | Self-reported Flow experience |
| **GEQ Immersion** (α = .82) | Sensory immersion |
| **NPS-3** (α = .76) | Perceived narrative personalization |
| **miniPXI** | Player experience (exploratory) |

</div>
<div>

### Qualitative component

- **20 semi-structured interviews** (10 per condition)
- Reflexive Thematic Analysis (Braun & Clarke, 2022)
- 47 initial codes → 4 final themes

### Statistical approach

- **Welch's *t*-test** (robust to unequal variance)
- **Bonferroni correction**: α_adj = .0167 for 3 hypotheses
- **Cohen's *d*** effect sizes with 95% CIs
- **Shapiro-Wilk** normality checks
- **Behavioural metrics** as demand-characteristic-free corroboration

### Demographics (final sample)

N = 49 (1 excluded: server crash). Mean age 22.2, 65% male. No baseline differences on age or gaming hours.

</div>
</div>

---

<!-- Slide 11: Quantitative Results (~2 min) -->

# Results: Quantitative Findings

<div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; text-align: center; margin-bottom: 1rem;">
<div class="kpi">
  <span class="stat" style="color: #27ae60;">d = 0.84**</span>
  <span class="label">NPS-3 Personalization<br/>p = .005 (survives Bonferroni)</span>
</div>
<div class="kpi">
  <span class="stat" style="color: #2980b9;">d = 0.65*</span>
  <span class="label">GEQ Flow<br/>p = .027 (misses Bonferroni)</span>
</div>
<div class="kpi">
  <span class="stat" style="color: #95a5a6;">d = 0.38</span>
  <span class="label">GEQ Immersion<br/>p = .187 (n.s.)</span>
</div>
</div>

| Measure | Exp. *M* (*SD*) | Ctrl. *M* (*SD*) | Cohen's *d* | *p* | Bonferroni? |
|---|---|---|---|---|---|
| **NPS-3** | 4.92 (1.18) | 3.88 (1.31) | **0.84** | **.005** | **Survives** |
| **GEQ Flow** | 2.78 (0.62) | 2.36 (0.68) | **0.65** | .027 | Misses |
| GEQ Immersion | 2.64 (0.71) | 2.38 (0.66) | 0.38 | .187 | No |

### Behavioural corroboration (participants unaware these were measured)

| Metric | Exp. | Ctrl. | *d* | *p* |
|---|---|---|---|---|
| **Dialogue read ratio** | 0.72 | 0.58 | **0.87** | .004 |
| Voluntary NPC interactions | 8.4 | 6.2 | **0.75** | .012 |

---

<!-- Slide 12: Qualitative Results (~1.5 min) -->

# Results: Qualitative Themes

20 interviews analysed via Reflexive Thematic Analysis (Braun & Clarke, 2022):

<div class="finding">

**Theme 1: "The story pays attention"** (8/10 Exp.)
Ambient sense that the narrative noticed and responded to *how* they played. Metaphor of being "seen" by the game.
*"It felt like the game knew I was exploring. The Chronicler started telling me things that matched what I was actually doing."* — P07

</div>

<div class="finding">

**Theme 2: "Tone matching"** (6/10 Exp.)
Urgent dialogue during combat; lore-rich content during exploration. Players noticed and valued the alignment.
*"When I was struggling with the enemies, the dialogue got more urgent, more helpful. That felt right."* — P12

</div>

<div class="limitation">

**Theme 3: "Generic narrative as wallpaper"** (7/10 Ctrl.)
Static narrative perceived as irrelevant, not bad. Gradual disengagement. Corroborates 58% dialogue read ratio.

</div>

<div class="limitation">

**Theme 4: "Occasional dissonance"** (4/10 Exp.)
Tone mismatch during rapid state transitions. Root cause: 5-second telemetry lag.

</div>

**No participants** in either condition described the narrative as obviously machine-generated.

---

<!-- Slide 13: Discussion & Limitations (~1.5 min) -->

# Discussion and Limitations

### What the pattern means

**Strong personalization → moderate Flow → weak immersion** is internally coherent:
- The system directly manipulates narrative content (NPS-3 captures this)
- This manipulation has a downstream effect on Flow (the PPO optimisation target)
- Immersion depends on factors the system does not control (visuals, audio, polish)

### Honest limitations

<div class="columns">
<div>

- **PPO trained in simulation**, not on real player data. Markovian assumption almost certainly violated in practice
- **Hexad profiling is rule-based**; no ground-truth questionnaire validation. Cannot distinguish intentional from incidental behaviour
- **Phi-3.5 Mini** (3.8B) constrains narrative quality relative to larger models

</div>
<div>

- **Single 30-minute session**; cumulative effects invisible
- **Prototype testbed**, not a commercial game; limits ecological validity
- **N = 49**; powered for medium effects, blind to small ones
- **NPS-3** is a custom scale without independent validation

</div>
</div>

### Threats to validity

**Internal**: demand characteristics (mitigated by blind design, corroborated by behavioural metrics)
**Construct**: GEQ is retrospective; NPS-3 unvalidated
**External**: prototype game, convenience sample

---

<!-- Slide 14: Contributions, SPER, Future Work (~2 min) -->

# Contributions, Ethics, and Future Work

<div class="columns">
<div>

### Six original contributions

1. **Telemetry-derived Hexad profiles** — no questionnaire; within-session updating
2. **Dynamic RAG-grounded narrative** — lore context selected at runtime by player state
3. **Episodic session memory** for real-time game narrative (first application)
4. **PPO for narrative action selection** — reframes RL from mechanical DDA to story
5. **Flow-based MDP reward** — principled theoretical grounding
6. **Complete closed-loop integration** — five modules in one deployable Unity plugin

### Future directions

- Validate Hexad proxies against questionnaire ground truth
- **Online RL**: policy updates from real player data
- Larger LLMs + domain fine-tuning
- Multi-session longitudinal study
- Deployment in a commercial game context

</div>
<div>

### SPER Considerations

**Social**: Player profiling raises questions about behavioural surveillance in games. Flow-sustaining systems nudge psychological states; this is a mild form of manipulation, acknowledged openly

**Professional**: System runs entirely locally. Open-weight models, no commercial API dependency. All code, instruments, and analysis scripts included in submission

**Ethical**: Informed consent obtained; participants debriefed post-session. SPER form approved (14 Nov 2025; supervisor affirmed 21 Nov 2025). No deception beyond condition blinding

**Legal & Security**: Telemetry stored locally in SQLite; no PII beyond session IDs. No data leaves the device. GDPR-compliant by design (no cloud transmission)

</div>
</div>

---

<!-- Slide 15: Closing & Q&A -->

# Thank You — Questions?

**Rivindu Bopage** &ensp;|&ensp; RGU: 2312553 &ensp;|&ensp; IIT: 20220580
Supervisor: Ms. Bimali Wickramasinghe

<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-top: 1rem;">
<div>

### Key numbers

| | |
|---|---|
| **N = 49** | Between-subjects study |
| **d = 0.84** | Personalization (NPS-3) |
| **d = 0.65** | Flow (GEQ) |
| **d = 0.87** | Dialogue read ratio |
| **5 modules** | Closed-loop pipeline |
| **8 actions** | PPO narrative selection |
| **5-second** | Telemetry cycle |
| **23 signals** | Per telemetry window |

</div>
<div>

### One-sentence summary

A closed-loop Unity plugin that wires player modelling, RL adaptation, RAG-grounded LLM generation, and episodic memory into one system. Players perceived the resulting narrative as significantly more personalized (*d* = 0.84, *p* = .005), and that perception was corroborated by what they actually did during play.

### Stack

FastAPI + Python · Unity 6 · Phi-3.5 Mini via Ollama · Stable-Baselines3 PPO · sentence-transformers · SQLite

</div>
</div>