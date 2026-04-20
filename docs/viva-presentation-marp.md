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
  .highlight { background: #f5f0e0; border-left: 4px solid #c8a951; padding: 12px; border-radius: 4px; }
  .stat { font-size: 36px; font-weight: bold; color: #1a1a2e; }
  .label { font-size: 16px; color: #666; }
  .rq { background: #f0f4f8; border-left: 4px solid #1a1a2e; padding: 8px 12px; margin: 6px 0; border-radius: 2px; font-size: 22px; }
  footer { font-size: 14px; color: #999; }
---

<!-- Slide 1: Title -->
# Dynamic Narrative Personalization in Games
### A Closed-Loop System Using Player Modelling and RL-Guided LLM Generation

**Rivindu Bopage**
RGU ID: 2312553 | IIT ID: 20220580

BSc Artificial Intelligence and Data Science
CM4609 Individual Research Project
Robert Gordon University

---

<!-- Slide 2: Problem & Motivation (~2 min starts here) -->
# The Problem

Current game narrative systems are **static**: they do not adapt their tone, urgency, or content to the psychological state and demonstrated preferences of an individual player in real time.

<div class="columns">
<div>

### What players experience
- A bored player gets the same low-stakes text as an engaged one
- An anxious player gets no narrative guidance
- An explorer sees the same sparse text as someone who skips dialogue

</div>
<div>

### Why it matters
- **Self-Determination Theory** (Ryan & Deci, 2000): perceived competence, autonomy, and relatedness sustain engagement
- Narrative is a direct vehicle for signalling all three
- Yet game analytics pipelines are used for monetisation, not real-time content adaptation

</div>
</div>

---

<!-- Slide 3: Research Gap & Questions -->
# Research Gap and Questions

### No prior work integrates all of these in one system:
Telemetry-derived Hexad profiling + Flow-state RL reward + RAG-grounded LLM generation + Episodic memory

| Prior Work | What It Does | What It Lacks |
|---|---|---|
| **PANGeA** (Todd et al., 2024) | LLM narrative from game state | No player model, no RL |
| **LIGS** (Kumaran & Riedl, 2025) | LLM pipeline coherence | No player modelling, no adaptation |
| **Authored branching** (Mass Effect, BG3) | Choice-driven narrative | No behavioural response, combinatorial cost |

<div class="rq"><b>RQ1:</b> Can a closed-loop AI system produce narrative players perceive as more personalized?</div>
<div class="rq"><b>RQ2:</b> Does PPO-driven adaptation lead to measurably higher Flow?</div>
<div class="rq"><b>RQ3:</b> How do players experience dynamically personalized narrative?</div>

---

<!-- Slide 4: Literature Foundation (~2 min) -->
# Literature Foundation

<div class="columns">
<div>

### Six domains feed the design

1. **Player Modelling** (Bartle, Hexad, player2vec)
2. **Flow Theory** (Csikszentmihalyi's challenge-skill balance)
3. **Narrative Personalization** (Facade, Tracery, branching)
4. **LLMs for Games** (PANGeA, LIGS, RAG)
5. **Reinforcement Learning** (DDA, PPO)
6. **Episodic Memory** (EM-LLM)

</div>
<div>

### Key theoretical grounding

- **Hexad** (Tondello et al., 2016): 6 player motivation types; always administered via questionnaire until now
- **Flow** (Csikszentmihalyi, 1990): optimal experience when challenge matches skill
- **PPO** (Schulman et al., 2017): used for mechanical DDA; never before for narrative action selection

</div>
</div>

<div class="highlight">

**The gap is integration, not invention.** Each technique exists; what has not appeared is the closed loop.

</div>

---

<!-- Slide 5: System Architecture (~3 min starts here) -->
# System Architecture

Five modules form a closed-loop pipeline, cycling every 5 seconds:

```
Player Behaviour → [M1] Telemetry Collection → [M2] Player Modelling
  → [M3] PPO Adaptation → [M4] Narrative Generation → [M5] Content Injection → Player
```

| Module | Component | Technology |
|---|---|---|
| **M1** Telemetry Collection | PlayerDataLogger | Unity C#, WebSocket |
| **M2** Player Modelling | FeatureExtractor, HexadProfiler, FlowClassifier | Python, rule-based |
| **M3** Adaptation Engine | NarrativeAgent (PPO) | Stable-Baselines3, Gymnasium |
| **M4** Narrative Generation | LoreRetriever, EpisodicMemory, PromptBuilder | sentence-transformers, Ollama |
| **M5** Content Injection | NarrativeManager, ContentInjector | Unity C#, UnityEvents |

Platform split: **Unity client** (M1 + M5) communicates with **FastAPI backend** (M2 + M3 + M4)

---

<!-- Slide 6: Player Modelling Module -->
# Player Modelling: Hexad + Flow

<div class="columns">
<div>

### Hexad from Telemetry (no questionnaire)

23 behavioural signals per 5-second window are reduced to **11 features**, then mapped to **6 continuous Hexad scores**:

| Hexad Type | Key Signals |
|---|---|
| Achiever | KD ratio, objective rate |
| Explorer | Explore rate, lore engagement |
| Socialiser | NPC interactions, dialogue |
| Philanthropist | Voluntary help events |
| Player (competitive) | Damage dealt, ability accuracy |
| Disruptor | Deaths, idle ratio |

</div>
<div>

### Flow Classification

Rule-based decision tree using **challenge-skill ratio**:

- **FLOW**: ratio near 1.0, engagement high
- **BOREDOM**: ratio < 0.6, challenge too low
- **ANXIETY**: ratio > 1.8, challenge too high
- **APATHY**: both scores low, disengaged

Sliding window: last 6 batches (~30 seconds) for Flow; full session for Hexad

</div>
</div>

---

<!-- Slide 7: Adaptation Engine (PPO MDP) -->
# RL-Based Adaptation: PPO for Narrative

### MDP Formulation

- **State**: (FlowState, HexadProfile) = 4 discrete + 6 continuous dimensions
- **Actions**: 8 narrative modulations

| Action | Description |
|---|---|
| RAISE_STAKES / LOWER_STAKES | Adjust narrative tension |
| ADD_MYSTERY / ADD_HUMOR | Shift narrative tone |
| PROVIDE_GUIDANCE | Help text for struggling players |
| INCREASE_URGENCY | Pace acceleration |
| LORE_REWARD | Deep world-building for explorers |
| NO_CHANGE | Maintain current direction |

### Flow-Based Reward

`+1.0 FLOW` | `-0.3 BOREDOM` | `-0.5 ANXIETY` | `-0.8 APATHY`
Plus: streak bonus (+0.2), transition bonus (+0.3), repetition penalty (-0.15)

**Cold-start heuristic** for first 120s before PPO policy activates

---

<!-- Slide 8: Narrative Generation (RAG + Memory) -->
# Narrative Generation: RAG + Episodic Memory

<div class="columns">
<div>

### RAG Pipeline
- **Lore corpus**: ~30 paragraphs (world, characters, quests)
- **Embedding**: all-MiniLM-L6-v2 (sentence-transformers)
- **Retrieval**: in-memory numpy cosine similarity
- **Dynamic context**: same location, different Flow state = different lore passages retrieved

### LLM
- **Phi-3.5 Mini** (3.8B) via Ollama
- Runs locally: no cloud dependency, predictable latency
- Structured prompt: player state + lore context + memory + action directive

</div>
<div>

### Episodic Session Memory
- Inspired by EM-LLM (Fountas et al., 2024)
- Importance-weighted: keeps significant narrative events, discards routine ones
- Gives the LLM compressed history so generated content can:
  - Reference prior events
  - Maintain character continuity
  - Avoid contradicting what the player experienced

**First application of episodic memory compression to real-time game narrative.**

</div>
</div>

---

<!-- Slide 9: Implementation & Demo (~5 min starts here) -->
# Implementation

### Technology Stack

<div class="columns">
<div>

**Backend** (Python 3.12)
- FastAPI with 4 routers
- SQLite for telemetry persistence
- Stable-Baselines3 for PPO
- sentence-transformers for RAG embeddings
- Ollama HTTP client for LLM inference

</div>
<div>

**Unity Plugin** (C# / Unity 6)
- UPM package: `com.research.narrative-plugin`
- `PlayerDataLogger`: 23-signal telemetry every 5s
- `NarrativeManager`: polls `/api/narrative`
- `ContentInjector`: fires UnityEvents
- Testbed: 3D RPG on AnyRPG Core framework

</div>
</div>

### Key Design Decisions
- **Local LLM only**: privacy, no network dependency during study
- **In-memory RAG**: corpus small enough; no external vector DB needed
- **Cold-start heuristic**: rule-based fallback for first 120s before PPO has enough data

---

<!-- Slide 10: Live Demo / Demo Walkthrough -->
# System Demo

### What the demo shows:

1. **Player walks around** the Eryndal world; telemetry streams every 5 seconds
2. **Backend logs** show Hexad profile updating, Flow state classification
3. **After ~120 seconds**: PPO policy activates, selects narrative action
4. **Narrative text** appears in bottom HUD panel (TMPro, auto-dismiss with fade)
5. **Tone shifts** visible when gameplay changes (combat vs. exploration)

### The closed loop in action:

```
[Explorer behaviour detected] → Hexad: Explorer=0.82 → Flow: FLOW
  → PPO selects: LORE_REWARD → RAG retrieves: Eryndal ruins lore
  → LLM generates: "The ancient glyphs along the corridor walls..."
  → HUD displays narrative → Player reads → Read ratio tracked
```

*If live demo is not possible: recorded walkthrough video showing the full 5-module cycle.*

---

<!-- Slide 11: Results — Quantitative (~4 min starts here) -->
# Results: Quantitative Findings

**Between-subjects study: N = 49** (25 Experimental, 24 Control; 1 excluded for technical failure)

| Measure | Exp. M (SD) | Ctrl. M (SD) | Cohen's *d* | *p* | Bonferroni |
|---|---|---|---|---|---|
| **NPS-3 Personalization** | 4.92 (1.18) | 3.88 (1.31) | **0.84** | **.005** | Survives |
| **GEQ Flow** | 2.78 (0.62) | 2.36 (0.68) | **0.65** | .027 | Misses (.0167) |
| GEQ Immersion | 2.64 (0.71) | 2.38 (0.66) | 0.38 | .187 | No |

### Behavioural evidence (demand-characteristic-free)

| Metric | Exp. | Ctrl. | *d* |
|---|---|---|---|
| **Dialogue read ratio** | 0.72 | 0.58 | **0.87** |
| Voluntary NPC interactions | 8.4 | 6.2 | **0.75** |

**Pattern**: strong personalization (*d* = 0.84), moderate Flow (*d* = 0.65), weak immersion (*d* = 0.38)

---

<!-- Slide 12: Results — Qualitative Themes -->
# Results: Qualitative Themes

**20 interviews (10 Exp., 10 Ctrl.)** analysed via Reflexive Thematic Analysis (Braun & Clarke, 2022)

| Theme | Who | Finding |
|---|---|---|
| **"The story pays attention"** | 8/10 Exp. | Ambient sense of being "noticed" by the narrative |
| **"Tone matching"** | 6/10 Exp. | Urgent dialogue during combat, lore-rich content during exploration |
| **"Generic narrative as wallpaper"** | 7/10 Ctrl. | Gradual disengagement; text was "fine, just not about what I was doing" |
| **"Occasional dissonance"** | 4/10 Exp. | Mismatched tone during rapid state transitions (5s telemetry lag) |

<div class="highlight">

**No participants** in either condition described the narrative as obviously machine-generated. The RAG grounding and structured prompts maintained the fictional frame.

</div>

---

<!-- Slide 13: Discussion & SPER -->
# Discussion, Limitations, and Ethics

<div class="columns">
<div>

### What the results mean
- **NPS-3** (*d* = 0.84): system produces clearly perceptible personalization
- **Flow** (*d* = 0.65): narrative tone can influence psychological state (extends DDA literature)
- **Immersion** (*d* = 0.38): 30-min session + prototype visuals insufficient to move this broader construct

### Key limitations
- PPO trained in simulation, not on real player data
- Hexad profiling is rule-based; no ground-truth validation
- Phi-3.5 Mini constrains narrative quality
- Single 30-minute session; no cumulative effects
- N = 49 underpowered for small effects

</div>
<div>

### SPER Considerations

**Social**: Player profiling raises questions about behavioural surveillance in games

**Professional**: System runs entirely locally; no data leaves the device. Open-weight models, no commercial API dependency

**Ethical**: Informed consent obtained; participants debriefed. Manipulation of psychological states (nudging toward Flow) is mild but acknowledged

**Legal/Security**: SQLite telemetry stored locally; no PII beyond session IDs. GDPR-compliant by design (no cloud transmission)

</div>
</div>

---

<!-- Slide 14: Contributions, Future Work, Conclusion (~2 min) -->
# Contributions and Future Work

### Six original contributions

1. **Telemetry-derived Hexad profiles** (no questionnaire; within-session updating)
2. **Dynamic RAG-grounded narrative** (context selected at runtime by player state)
3. **Episodic session memory** for real-time game narrative (first application)
4. **PPO for narrative action selection** (reframes RL from mechanical DDA to story)
5. **Flow-based MDP reward** (principled theoretical grounding)
6. **Complete closed-loop integration** as a deployable Unity plugin

### Future directions

- Empirical validation of Hexad proxies against questionnaire ground truth
- **Online RL**: continue policy updates from real player data
- Larger LLMs and domain fine-tuning for richer narrative
- Multi-session longitudinal study
- Deployment in a commercial game context

<div class="highlight">

**Summary**: A closed-loop system that makes game narrative pay attention to the player. The integration is feasible, the personalization is perceptible (*d* = 0.84), and the approach opens a design space that prior work left unexplored.

</div>

---

<!-- Slide 15: Thank You / Q&A -->
# Thank You

### Questions?

**Rivindu Bopage**
RGU ID: 2312553 | IIT ID: 20220580

<div class="columns">
<div>

### Key numbers to remember
- **N = 49** (between-subjects)
- **d = 0.84** (personalization)
- **d = 0.65** (Flow)
- **d = 0.87** (dialogue read ratio)
- **8 narrative actions**, 5-second cycle
- **5 modules** in closed loop

</div>
<div>

### Repository & materials
- Backend: FastAPI + Python 3.12
- Plugin: Unity 6 UPM package
- LLM: Phi-3.5 Mini (3.8B) via Ollama
- All code, lore corpus, questionnaires, and analysis scripts included in submission

</div>
</div>