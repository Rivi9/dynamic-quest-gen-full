# Viva Voce Script — CM4609 Individual Research Project

**Candidate:** Rivindu Bopage (RGU 2312553 · IIT 20220580)
**Supervisor:** Ms. Bimali Wickramasinghe
**Project:** Dynamic Narrative Personalization in Games Using AI
**Session:** 20 min presentation + 15–20 min Q&A (60 min total)

---

## Pre-Viva Checklist

- Arrive 15 minutes early; slides open (`viva-presentation-marp.pdf`), backup on USB
- Demo video pre-loaded (no live Ollama — too risky)
- Printed handout of key numbers (optional)
- Water, phone silenced
- Stand; speak to the panel, not the screen; never read verbatim

---

## Known Slide/Thesis Discrepancies — Be Ready

Two points where the slides are slightly at odds with the thesis and paper. An examiner who has read the thesis carefully may catch them.

- **Slide 6 — APATHY Flow threshold.** The slide shows `ratio < 0.60`. The thesis and paper define APATHY as `idle > 0.40 AND dialogue_engage < 0.30 AND ratio < 0.75`. If asked: *"Good catch — the thesis and paper are authoritative. The slide value is a typo; I'll correct it."* Do not defend the slide.
- **Slide 10 — final sample split.** The slide reads "25 Experimental, 25 Control" under design, and "N = 49 (1 excluded)" under demographics. The post-exclusion split is **25 Experimental, 24 Control** — the excluded participant was in Control. Say it that way if asked.

---

## Opening (before clicking the first slide) — 15 seconds

> "Good morning/afternoon. Thank you for examining this project. I'll spend about twenty minutes walking through the research and the system I built, then I'll hand over to questions."

Pause. Click to Slide 1.

---

## Slide 1 — Title (~20 seconds)

> "The project is called *Dynamic Narrative Personalization in Games Using AI*. It's my BSc Final Year Project, supervised by Ms. Bimali Wickramasinghe at IIT in collaboration with Robert Gordon University."

Keep it short. The panel has the title in front of them.

---

## Slide 2 — The Problem (~2 min)

> "Let me start with the problem. Game narrative today is overwhelmingly **static**. Whether you are a methodical explorer who reads every codex entry, or a player who rushes combat and skips dialogue, you hear the same village elder say the same warning in the same tone.
>
> That's not just an aesthetic complaint. The narrative is the single biggest pool of *contextual* content in most games, and it has no sensor wired to how the player is actually experiencing the session. When challenge exceeds skill, the story doesn't notice. When a curious player veers off the critical path, the lore doesn't reward them. The experience is decoupled from the player's psychology.
>
> The opportunity is to close that loop: to let the narrative respond not only to explicit choices, but to behavioural signals — in effect, to use story as a lever for shaping engagement."

Land on the highlight box: *"narrative as a lever for optimal experience."*

**Transition:** "Prior work has touched pieces of this, but never the whole loop. Let me show you what I mean."

---

## Slide 3 — Literature & Research Gap (~2 min)

> "The literature clusters into three camps.
>
> **Authored branching** — games like *Baldur's Gate 3* and *Disco Elysium*. Enormous narrative depth, but the branching is triggered by explicit player choices. It does not respond to how the player is behaving in between those choices.
>
> **Procedural generation** — tools like Tracery, or the Expressionist system. These generate surface variation, but they carry no player model. There is no psychological sensing loop.
>
> **LLM-driven narrative** — the most recent direction. PANGeA at AAAI 2024 is a good representative. LLMs are used to generate in-game content, but the prompts are static, there's no RL adaptation, and no episodic memory of what has already been told to this player.
>
> The gap, I argue, is **integration, not invention**. Each of the pieces exists in isolation — player modelling, Flow theory, reinforcement learning, RAG, episodic memory. What has not been done is to wire them into a single closed loop running in a deployable game.
>
> That's what this project does."

**Transition:** "So the research questions follow directly from that gap."

---

## Slide 4 — Research Questions (~1.5 min)

Read each RQ *slowly*, then explain what it tests:

> "RQ1 asks whether the full closed-loop system produces narrative that players **perceive as more personalized** than static narrative. That's the construct I'm primarily trying to manipulate.
>
> RQ2 asks whether that manipulation **translates into higher Flow experience**, which is the downstream effect the system is optimising for.
>
> RQ3 is the qualitative complement: **how do players describe** their experience of this narrative, beyond what scales can capture?
>
> The study design is **between-subjects**, target N of 50, with Welch's *t*-test for primary hypotheses and a Bonferroni correction at α equals 0.0167 for the three primary tests."

**Transition:** "Let me show you how the system is put together."

---

## Slide 5 — System Architecture (~2 min)

> "The pipeline is five modules, and it closes the loop every five seconds.
>
> It starts at Module 1: the Unity client emits 23 telemetry signals — kills, deaths, dialogue read, tiles explored, damage dealt, idle time, and so on — over a WebSocket.
>
> Module 2 is the player model on the Python backend. A feature extractor turns those 23 signals into 11 normalised features. A rule-based Hexad profiler maps those features to six continuous Hexad scores. A decision-tree Flow classifier assigns one of four states: Flow, Boredom, Anxiety, or Apathy.
>
> Module 3 is the PPO agent. Given the (Flow, Hexad) state, it picks one of eight narrative actions — raise stakes, provide guidance, lore reward, and so on.
>
> Module 4 turns that action into actual text. A RAG pipeline retrieves the top-three relevant lore passages, episodic memory contributes the five most important prior events, and a prompt builder hands the whole thing to Phi-3.5 Mini running locally in Ollama.
>
> Module 5 closes the loop: the generated narrative is pushed back to Unity, where a content injector displays it on a HUD panel.
>
> The split matters: Unity handles only M1 and M5. Everything in the middle is a Python backend. That's deliberate — it lets the plugin drop into any Unity project without shipping Python with it."

**Transition:** "Let me walk through the three modules that do the heavy lifting — starting with the player model."

---

## Slide 6 — Player Modelling (~2 min)

> "The Hexad framework — Achiever, Explorer, Socialiser, Free Spirit, Disruptor, Philanthropist — is traditionally measured with a questionnaire. In a real-time game loop, that is useless.
>
> What I do instead is define **behavioural proxies** for each dimension. Explorer, for instance, is weighted toward map coverage and lore engagement. Disruptor is weighted toward kills and damage dealt. Each of the six dimensions is a weighted combination of features, and the weights come from the Hexad design paper's mapping of behaviour to motivation.
>
> I want to be careful here: these are **proxies, not measurements**. I make that limitation explicit in Chapter 5. A player might *explore* because they enjoy exploration, or because they are lost. My system can't tell those apart. But the proxy is stable enough to drive adaptation, and it avoids interrupting play with a questionnaire.
>
> On the right is the Flow classifier. It's a rule-based decision tree on the challenge-to-skill ratio — a direct operationalisation of Csikszentmihalyi's original model. The thresholds, 0.75 and 1.30, were set empirically during pilot testing.
>
> The primary novelty claim here is that this is the first system, to my knowledge, to derive Hexad profiles **entirely from telemetry, with within-session updating**. Every prior system either used a questionnaire or fixed the profile at session start."

**Transition:** "That gives us the state. The next piece decides what to do with it."

---

## Slide 7 — RL Adaptation Engine (~1.5 min)

> "The adaptation is a PPO agent trained on a Gymnasium MDP I built specifically for this. State is a seven-dimensional continuous vector — an encoded Flow state, the normalised challenge-skill ratio, and four Hexad dimensions: Explorer, Socialiser, Achiever, Disruptor. I deliberately excluded Free Spirit and Philanthropist from the state as a dimensionality reduction; their signals are largely captured by the other components, and keeping them in blew up training time without changing the policy. The action space is eight narrative modulations — raise stakes, add mystery, provide guidance, lore reward, and so on.
>
> The reward function is **Flow-based and graduated**. Flow gives a full positive reward of 1.0. Boredom and Anxiety give moderate negative rewards. Apathy — the worst state, where the player is neither engaged nor challenged — gets the strongest penalty. That graduation matters; treating all non-Flow states the same produced degenerate policies during training.
>
> Secondary reward shaping: a streak bonus for sustained Flow, a transition bonus for recovering from Apathy, a step penalty to discourage indecision, and a repetition penalty to discourage hammering the same action.
>
> There's a cold-start problem — PPO needs state history to act sensibly. For the first 120 seconds, I fall back to a rule-based heuristic. If the classifier says Anxiety, the heuristic picks PROVIDE_GUIDANCE, and so on. After 120 seconds, control passes to PPO."

**Transition:** "Once PPO picks an action, it has to become text. That's Module 4."

---

## Slide 8 — Narrative Generation (~1.5 min)

> "Generation has three ingredients.
>
> First, **RAG**. I have a small lore corpus — about thirty paragraphs covering the world, the characters, and the quests. They're embedded using all-MiniLM-L6-v2, 384 dimensions, L2-normalised. At runtime I do an in-memory cosine similarity search and pull the top three chunks. Two things matter here: I chose **numpy over ChromaDB** because ChromaDB had a pydantic-v1 incompatibility with Python 3.14 that I couldn't work around, and because for a 30-paragraph corpus, numpy is faster. The second point is that the *same location* retrieves *different lore* depending on Flow state — that's what makes it dynamic rather than lookup-based.
>
> Second, **episodic memory**. This is inspired by EM-LLM from Fountas et al. last year. Events are stored with an importance score. The memory caps at 10 events, and when it fills, it evicts the lowest importance. The top five by importance go into the prompt. This gives the narrative cross-event continuity — characters remember the player.
>
> Third, the **LLM itself**. Phi-3.5 Mini via Ollama, running entirely locally. Output is JSON-constrained — two to four sentences, structured.
>
> I'll be blunt about the novelty claim here: episodic memory compression has been applied to long-document LLMs, but not to real-time game narrative. That's the contribution."

**Transition:** "That's the theory. Let me show you what it looks like when it runs."

---

## Slide 9 — Implementation (~2 min)

> "On the left, the backend. FastAPI with four routers. SQLite for telemetry persistence — I specifically did not use Postgres because I wanted zero installation burden for a reviewer cloning the repo. Stable-Baselines3 for PPO. sentence-transformers for RAG. An Ollama HTTP client for the LLM. Eight pytest files cover every layer.
>
> On the right, the Unity plugin. It's packaged as a Unity Package Manager — `com.research.narrative-plugin` — so it drops into any Unity 6 project. Three main components: `PlayerDataLogger` pushes the telemetry, `NarrativeManager` polls the backend, and `ContentInjector` fires a UnityEvent that any HUD can subscribe to.
>
> The testbed is AnyRPG Core — an open-source 3D RPG framework, which I forked and extended with a custom zone called Eryndal.
>
> The trace at the bottom is real output from a pilot session. Explore rate of 0.82, lore engagement 0.74. Hexad classifies as Explorer. Flow state is FLOW at confidence 0.91. PPO selects LORE_REWARD. RAG pulls ruins-related lore. The LLM generates the ancient glyph line. The HUD displays it. The player reads it — and that read event goes back into telemetry. That's the loop."

**If time permits, mention the demo video:**

> "I have a two-minute demo recording if the panel wants to see it in action after the Q&A."

**Transition:** "So the system works. The harder question is whether it *helps* — which brings us to evaluation."

---

## Slide 10 — Evaluation Design (~1.5 min)

> "Between-subjects study, target N of 50. Participants played a thirty-minute session. Experimental condition ran the full adaptive pipeline. Control condition ran the exact same game — same environment, same objectives, same NPCs — but with static narrative served from a `ScriptableObject`. Everything else identical. Participants were blind to condition.
>
> Four instruments. GEQ Flow and Immersion subscales, the validated measures. A custom three-item NPS-3 scale for perceived personalization — I'll defend that choice if asked. And miniPXI for a broader exploratory view.
>
> On the qualitative side, I ran twenty semi-structured interviews, ten per condition, and analysed them with Reflexive Thematic Analysis per Braun and Clarke's 2022 methodology.
>
> Statistics: Welch's t-test because I couldn't assume equal variances. Bonferroni correction at 0.0167 across three primary hypotheses. Cohen's d for effect sizes, with 95% confidence intervals. Shapiro-Wilk for normality checks. And critically, I reported **behavioural metrics** — dialogue read ratio, voluntary NPC interactions — as a corroboration channel that is free of demand characteristics, because participants had no idea those were being measured.
>
> Final sample is 49: one participant excluded due to a server crash."

**Transition:** "Here's what the data said."

---

## Slide 11 — Quantitative Results (~2 min)

> "Three numbers to take away.
>
> **NPS-3**, personalization: Cohen's d of 0.84, p-value 0.005. That survives Bonferroni. It's a **large effect size**. Players in the experimental condition perceived the narrative as substantially more personalized than the control.
>
> **GEQ Flow**: d of 0.65, p of 0.027. That's a medium-to-large effect, statistically significant at the conventional 0.05 level, but it does **not** survive the Bonferroni correction at 0.0167. I want to flag that honestly.
>
> **GEQ Immersion**: d of 0.38, not significant. A small-to-medium effect direction, but the study wasn't powered to detect it.
>
> The behavioural metrics are the reassurance line. Dialogue read ratio: experimental 72%, control 58%, d of 0.87. Voluntary NPC interactions: experimental 8.4, control 6.2, d of 0.75. Both effects are large, and both are **free of the demand characteristics** that can inflate self-report. Participants didn't know these were metrics. They just behaved.
>
> The pattern — strong self-report, strong behaviour, weaker Flow, flat Immersion — is **internally coherent**, and I'll unpack that coherence on the Discussion slide."

**Transition:** "The interviews tell us *why* the numbers look like this."

---

## Slide 12 — Qualitative Results (~1.5 min)

> "Four themes from the twenty interviews.
>
> **Theme 1** — eight out of ten experimental participants described an ambient feeling that the narrative was *watching*. Not literally, but metaphorically: 'the story noticed what I was doing.' P07: 'It felt like the game knew I was exploring.'
>
> **Theme 2** — six out of ten noticed tone matching. Combat dialogue became urgent. Exploration dialogue became lore-heavy. P12: 'When I was struggling, the dialogue got more urgent. That felt right.'
>
> **Theme 3** — seven out of ten *control* participants described the static narrative as **wallpaper**. Not bad, not offensive — just irrelevant. That corroborates the 58% dialogue read ratio. They stopped reading because they decided it wasn't worth reading.
>
> **Theme 4** — four out of ten experimental participants noticed *dissonance* during rapid state transitions. The root cause is the five-second telemetry window: if a player's state changes faster than five seconds, the narrative lags behind.
>
> The critical negative finding: **nobody in either condition** described the narrative as obviously machine-generated. The LLM passes the smell test."

**Transition:** "So how do I interpret this overall pattern?"

---

## Slide 13 — Discussion and Limitations (~1.5 min)

> "The pattern — strong personalization, moderate Flow, weak Immersion — is not contradictory, it's mechanistically coherent.
>
> The system **directly** manipulates narrative content. NPS-3 captures that directly. That's where the largest effect sits.
>
> Flow is the **downstream** effect. PPO optimises toward it, but it has to route through narrative. Smaller effect, as expected.
>
> Immersion depends on things the system doesn't control — visuals, audio, polish. We shouldn't expect a narrative-only intervention to move it much.
>
> On limitations, I want to lead with the most important ones. PPO was trained in simulation, not on real player data. The Markovian assumption is almost certainly violated in practice — player states are not memoryless. Hexad is rule-based and lacks ground-truth validation. Phi-3.5 Mini is a small model; larger models would produce richer prose. The study is a single thirty-minute session, so cumulative effects across a multi-hour playthrough are invisible. N of 49 is powered for medium effects and blind to small ones. And NPS-3 is a custom scale without independent validation — I'll defend it if asked, but it's an honest limitation."

**Transition:** "Let me close with what this contributes, the ethics, and where it goes next."

---

## Slide 14 — Contributions, Ethics, Future Work (~2 min)

> "Six original contributions, ordered by what I think is most defensible to least:
>
> **One:** telemetry-derived Hexad profiles with within-session updating, avoiding questionnaires. **Two:** dynamic RAG where the *same location* retrieves *different lore* conditional on player state. **Three:** episodic session memory applied to real-time game narrative. **Four:** PPO as a narrative action selector rather than a dynamic difficulty adjustment. **Five:** a Flow-based MDP reward with principled theoretical grounding. **Six:** the complete closed-loop integration — all five modules, deployable as a Unity plugin.
>
> On **SPER**: player profiling is a form of behavioural surveillance, and Flow-sustaining systems are a mild form of psychological nudging. I acknowledge that openly. The system runs entirely locally — Ollama, SQLite, no cloud — so there's no data leaving the device. No PII is collected beyond a session identifier. The SPER form was approved on the 14th of November 2025 and the supervisor affirmed on the 21st of November. Informed consent and post-session debrief for all participants.
>
> On **future work**: the four priorities are validating Hexad proxies against a real questionnaire, moving PPO to online policy updates from real players, swapping in larger fine-tuned LLMs, and running a multi-session longitudinal study. In the longer term, commercial game deployment."

**Transition:** "Thank you. I'm happy to take questions."

---

## Slide 15 — Thank You / Closing (~15 seconds)

> "The single-sentence summary is: I built a closed-loop Unity plugin that wires player modelling, reinforcement learning, RAG-grounded LLM generation, and episodic memory into one deployable system. Players perceived the resulting narrative as significantly more personalized, and that perception was corroborated by what they actually did during play."

Stand still. Don't click anything. Wait for the first question.

---

# Q&A Bank (by Category)

The panel is explicitly looking for: **research ownership, critical depth, technical mastery, ethical awareness.** Answers below are structured to hit all four.

---

## Category A — Methodology Choices

### Q: Why PPO specifically? Why not DQN or SAC?

> "Three reasons. First, the action space is **discrete with eight actions**, which PPO handles natively, whereas SAC is designed for continuous control. Second, PPO's clipped-objective updates are more stable than DQN's bootstrapped Q-values on small training budgets, and I was training on a single GPU for this thesis. Third, PPO is currently the most-reviewed baseline in RL-for-games literature, which made it the defensible choice for a thesis — anyone familiar with the field can assess what I did. I did consider A2C as a lighter alternative, but the sample efficiency was worse in my pilot training runs."

### Q: Why rule-based Flow classifier instead of ML?

> "Because I don't have labelled training data for Flow states. Csikszentmihalyi's model is already a decision rule on the challenge-to-skill ratio — it *is* a rule-based classifier by construction. Training a neural net on top would either need a questionnaire-labelled dataset, which I don't have, or self-supervised labels from the same rule, which is circular. If I were extending this for publication, I'd collect labelled Flow-state data via ESM — experience sampling — and then the ML approach would be justified."

### Q: Why Hexad instead of Big Five or OCEAN?

> "Hexad was specifically designed for games; Big Five is a general personality framework. Hexad's six dimensions — Achiever, Explorer, Socialiser, Free Spirit, Disruptor, Philanthropist — map cleanly onto observable gameplay behaviours. Big Five maps onto *dispositions* that require self-report. In a system whose core design constraint is no questionnaires mid-session, Hexad is the right framework. I discuss this in Chapter 3."

### Q: Why a custom NPS-3 scale? Why not use an existing validated one?

> "Because there isn't one. I searched. The closest existing instruments measure *game personalization* as a whole — the MPUQ, for instance — which conflates narrative with difficulty, visual customisation, and progression. I needed a three-item scale specifically on narrative personalization. NPS-3 reached Cronbach's alpha of 0.76 in this study, which is acceptable for a new scale, and the pattern of results was consistent with behavioural corroboration — so the construct validity is at least moderate. I am upfront in Chapter 5 that independent validation is a limitation."

### Q: Why N = 50? What was your power analysis?

> "G*Power a priori power analysis, two-tailed Welch's t-test, targeting Cohen's d of 0.5 — medium effect — with alpha at 0.05 and power at 0.80. That indicated n equals 25 per group, fifty total. The final sample of 49 after the technical exclusion is within that envelope. I was explicit in Chapter 3 that small effects would require a follow-up study with N around 200. I'd also note that the primary hypothesis — personalization — landed at d of 0.84, well above the target, so the study was sufficiently powered for the effect it was built to detect."

### Q: Why 5-second telemetry cycle?

> "Empirical pilot testing. Shorter than 3 seconds produced noisy Hexad scores because features hadn't accumulated enough signal. Longer than 7 seconds made adaptation feel laggy in qualitative pilot feedback. Five seconds was the sweet spot where both the features were stable *and* the adaptation felt responsive. Theme 4 of the qualitative findings — the 'occasional dissonance' — is directly traceable to this choice; it's a trade-off I made consciously."

### Q: Between-subjects vs within-subjects — why?

> "Carryover. If participants played both the adaptive and static conditions back-to-back, they would notice the contrast directly, which would inflate the effect. Between-subjects isolates condition without carryover, at the cost of needing higher N. For the sample size I could realistically recruit, I judged the between-subjects design to produce more trustworthy effect sizes."

---

## Category B — Technical Depth

### Q: Walk me through the PPO training regime — hyperparameters, episodes, timesteps.

> "Stable-Baselines3 PPO with the MlpPolicy — two hidden layers of 64 units each. Learning rate 3e-4, batch size 64, n_steps 2048, 10 gamma epochs, clip range 0.2. 200,000 total timesteps using a 4-environment vectorised rollout. Each training episode was roughly 60 steps of simulated gameplay with randomised initial Hexad profiles, so the policy couldn't collapse into profile-specific behaviours. I logged mean episode reward and action entropy — entropy stabilised in the last quarter of training, which is when convergence looked stable."

### Q: How is the Flow reward actually computed in the MDP?

> "At each step, the classifier emits a Flow state. That state maps to a base reward — plus-1.0 for Flow, minus-0.3 for Boredom, minus-0.5 for Anxiety, minus-0.8 for Apathy. Then four modifiers: a +0.2 streak bonus if the current state equals the previous state *and* is Flow; a +0.3 transition bonus if the previous state was Apathy and the current is anything else; a -0.05 step penalty applied always, to discourage indecision; and a -0.15 repetition penalty if the same action was picked in the last three steps. The final reward is the sum. All coefficients are in config so they're reproducible."

### Q: What's your RAG chunking strategy?

> "The lore corpus is already structured into paragraphs averaging 80–120 words each, written as natural narrative units — world descriptions, character bios, quest setups. I treat each paragraph as a single chunk, no further splitting. For a 30-paragraph corpus I could afford that. If I scaled to thousands of paragraphs, I'd switch to a recursive character splitter with around 200-token chunks and 20-token overlap, which is the current LlamaIndex default. I discuss this trade-off in the thesis."

### Q: How do you prevent LLM hallucination?

> "Three layers. First, RAG grounds the generation in retrieved lore chunks — the prompt literally says 'use only information from the passages above.' Second, the output is JSON-constrained so structural hallucinations are caught at parse time; a malformed response triggers a retry. Third, post-generation I apply a lightweight lore-consistency filter — a substring check against named entities in the retrieved chunks. If the LLM mentions a character not in context, the generation is rejected and the action defaults to NO_CHANGE. I'd be happy to show the `ollama_client.py` code."

### Q: Why Phi-3.5 Mini? Why not a 7B or 13B model?

> "Deployment constraint. The Unity testbed already uses roughly 6GB of VRAM when running a 3D scene; Phi-3.5 Mini at 4-bit quantisation takes 2.3GB, which fits. A 7B model takes about 4–5GB and starts causing frame drops. For a thesis that wants to demonstrate *real-time* adaptation, I prioritised latency over prose quality. I acknowledge in Chapter 5 that narrative richness would improve substantially with a larger model — that's in future work."

### Q: What happens if the Ollama server crashes mid-session?

> "Two fallback layers. The `NarrativeManager` in Unity has a 3-second timeout on the HTTP call. On timeout, it falls back to the control-condition `ScriptableObject` narrative — so the player sees *something*, not a broken UI. Separately, the backend has a simple liveness probe: if three consecutive generations fail, the system logs the session as degraded, which I flag in analysis. In the study, one participant's session triggered exactly this and was the exclusion that brought N from 50 to 49."

### Q: How do you handle concurrent telemetry from multiple players?

> "I don't, in this prototype. The FastAPI backend is single-session — it assumes one Unity client per backend instance. For a commercial deployment I'd need per-session state isolation, which would mean moving the `EpisodicMemory` and `PlayerState` objects into a session-keyed dict, and likely swapping SQLite for Postgres. That's explicitly out of scope in Chapter 5."

### Q: Your Hexad weights — how did you set them?

> "They come from Marczewski's original Hexad behavioural mapping, with minor adjustments after pilot testing. The weights are in `config.py` so they're inspectable. I want to be clear that I did not learn the weights — they are designer-set. Learning them would require a large dataset of players with Hexad questionnaire labels, which is the validation study I recommend in Chapter 6."

### Q: Your PPO state uses only four Hexad dimensions, not six. Why drop Free Spirit and Philanthropist?

> "Deliberate dimensionality reduction. Free Spirit overlaps heavily with Explorer — off-critical-path behaviour is a dominant Explorer signal too — so including it adds covariance without new information. Philanthropist has the weakest behavioural proxies in my telemetry; it depends on pro-social signals that are sparse in a single-player RPG. Excluding both shrinks the state from nine dimensions to seven, which made training converge faster without degrading the policy. Both dimensions are still computed for the player model output — they just don't enter PPO's observation. This is documented in Chapter 3."

### Q: What's the end-to-end latency? Is it really real-time?

> "End-to-end — telemetry arrival to narrative display — averages between 1.2 and 2.8 seconds depending on LLM inference load. That's inside the five-second telemetry window, so the next batch doesn't arrive before the adaptation is ready. The LLM dominates: Phi-3.5 via Ollama takes roughly 0.8 to 2 seconds per generation. RAG is under 50 milliseconds for a 30-paragraph corpus. PPO inference is sub-millisecond. If I needed tighter latency, the first optimisation would be a smaller quantised model — currently 4-bit, a 2-bit variant would halve inference time with a quality trade-off."

---

## Category C — Results and Statistics

### Q: Flow missed Bonferroni. Is your result actually real?

> "That's the most important challenge to the findings, so let me be direct. Flow p-value is 0.027, which is below the conventional 0.05 but above the Bonferroni-adjusted 0.0167. If I apply the strictest interpretation, Flow is a null result. I report it that way in Chapter 4.
>
> However, three things weaken the null conclusion. First, the effect size is Cohen's d of 0.65, which is medium-to-large — it's not a 'noise' effect. Second, the behavioural corroboration — dialogue read ratio at d of 0.87 — is free of demand characteristics and consistent with the Flow direction. Third, the study was powered for the primary hypothesis of personalization, which succeeded at d of 0.84 and did survive Bonferroni. Flow was hypothesis number two.
>
> My honest summary is: this study gives strong evidence that players perceive the narrative as more personalized, and suggestive-but-not-definitive evidence that this translates into higher Flow. I don't overclaim it."

### Q: Your behavioural metrics weren't pre-registered — aren't you fishing?

> "They were specified in the SPER submission as 'behavioural corroboration metrics' before data collection began. The pre-specification is in the ethics form, not a formal pre-registration — I acknowledge pre-registration with a platform like OSF would have been stronger, and that's listed as a methodological improvement in Chapter 6. The metrics themselves are telemetry logs that the system was always collecting, so there is no selective reporting: all of them are in the results table."

### Q: Cronbach's alpha of 0.76 for NPS-3 — is that good enough?

> "Nunnally's conventional threshold for early-stage scale development is 0.70, which NPS-3 clears. For established scales, 0.80 is the preferred target. 0.76 is in the acceptable range for a three-item scale in its first validation — and three-item scales have a structurally harder time hitting higher alphas because the formula divides by k minus one. I would not claim this is a mature instrument; I would claim it has acceptable internal consistency for a first use."

### Q: Why Welch's t-test rather than Mann-Whitney?

> "Primary analysis was Welch's because Shapiro-Wilk did not reject normality for any of the primary DVs — all p-values above 0.05 — so the parametric test was valid and more powerful. As a robustness check, I ran Mann-Whitney U for all DVs and the pattern of significance was identical. Both are reported in the stats analysis script. I chose Welch as primary because it's more widely recognised in the games user research literature."

### Q: What are the 95% confidence intervals for your effect sizes?

> "For NPS-3, d of 0.84, CI 0.25 to 1.43 — excludes zero comfortably, which is why it survives Bonferroni. For GEQ Flow, d of 0.65, CI 0.08 to 1.22 — just excludes zero at the 95% level, consistent with missing Bonferroni. For GEQ Immersion, d of 0.38, CI minus 0.19 to 0.95 — straddles zero, consistent with the null result. For miniPXI, d of 0.52, CI minus 0.05 to 1.09 — again straddles zero narrowly. The CIs are in Table II of the paper and Chapter 4 of the thesis."

### Q: Could the result be Hawthorne effect?

> "Possible in principle, but three factors argue against it. First, both conditions knew they were being observed — the Hawthorne effect would apply to both, and it is the *difference* that matters. Second, participants were blind to condition. Third, the behavioural metrics pick up things participants didn't know were being measured — they're not going to Hawthorne-effect their dialogue read ratio if they don't know it's a measured variable. If Hawthorne were the explanation, it wouldn't predict the large behavioural effect."

### Q: How did you handle multiple comparisons for the behavioural metrics?

> "I didn't apply Bonferroni to the behavioural metrics because they are reported as **corroboration** of the primary hypotheses, not as independent tests. That's an intentional analytic choice — I explain it in Chapter 4. If someone wanted to treat them as primary, they'd need Bonferroni across five tests at 0.01, and both behavioural effects still survive that. I check this in the script."

---

## Category D — Research Gap and Novelty

### Q: Isn't this just PANGeA with extra steps?

> "Fair question. PANGeA uses LLMs for narrative generation, like I do, but the architecture is fundamentally different on three axes. PANGeA has no player model — no Hexad, no Flow classification; prompts are static templates. PANGeA has no RL — actions are not selected by a trained policy. And PANGeA has no episodic memory — each generation is context-free. My contribution is the integration: the closed loop that lets the story respond to *how* someone is playing, not just what they chose. PANGeA is a narrative generator; this is a narrative *adaptation* system."

### Q: What's genuinely new here? Each piece has been done.

> "Two things are genuinely new, and I want to defend them separately.
>
> First, **telemetry-derived Hexad profiles with within-session updating**. Every prior system I found either uses a questionnaire or fixes the profile at session start. This is the first to update it continuously from behaviour.
>
> Second, **episodic memory compression for real-time game narrative**. EM-LLM showed importance-based memory compression works for long-document LLMs. I show it works for a real-time game loop. That's an application contribution, not a theoretical one — but it's a valid contribution.
>
> The rest is integration work. I don't claim PPO is new, or RAG is new. I claim the specific composition is new, and I claim it works empirically."

### Q: How is this different from dynamic difficulty adjustment?

> "DDA operates on mechanical parameters — enemy HP, spawn rates, XP curves. This system operates on **narrative content** — tone, urgency, what lore is mentioned, which character speaks. The orthogonal axis is what matters. DDA assumes difficulty is the lever; this system assumes narrative is a separate lever, and the two could be combined additively. I discuss the composition in Chapter 6 as future work."

### Q: Why is this a contribution to AI research specifically, not just games?

> "Three reasons. First, it's an **applied RL contribution** — RL for narrative action selection, which is an underexplored application domain. Second, it's an **applied RAG contribution** — dynamic retrieval conditioned on a classifier output, not just on a query. Third, it's an **applied episodic memory contribution** — taking a technique developed for long-context LLMs and deploying it in a real-time loop. Each of these extends an AI technique into a domain it hasn't been deployed in. That's the contribution to AI, not just to games."

---

## Category E — Limitations and Threats

### Q: What's the single biggest limitation?

> "The Markovian assumption in the PPO MDP. The policy treats each state as memoryless given the current (Flow, Hexad) tuple, but in practice player experience has long-range dependencies — narrative fatigue, anticipation, surprise. The policy can't model those. Everything else is fixable with more data or a bigger model; this one is structural. I'd move to a POMDP formulation with an LSTM policy head, which is in Chapter 6 as future work."

### Q: Ecological validity — this is a prototype, not a real game.

> "Correct, and I don't hide from that. AnyRPG is a functional 3D RPG, so it's not toy-grade, but it's not a commercial product either. A player giving up thirty minutes for a thesis study is not the same as a player giving up forty hours for *Baldur's Gate*. What a thirty-minute prototype *can* do is isolate whether the intervention works under controlled conditions, which is what this study shows. What it *cannot* do is predict commercial success. I'm explicit that deployment in a commercial title is a future-work item."

### Q: Convenience sample — generalisability?

> "University students, 65% male, mean age 22. That's a narrow slice. Two effects: the age range may exaggerate responsiveness to narrative adaptation because younger players are more tolerant of experimental mechanics; and the gender skew means this says less than it should about how female or non-binary players experience the system. Both are in the limitations section. Extending to a broader sample with age, gender, and gaming-experience stratification is in future work."

### Q: Demand characteristics — how did you mitigate?

> "Four ways. First, participants were **blind to condition** — they weren't told whether their narrative was adaptive or static. Second, the **instruments were masked** — the consent form described the study as 'an evaluation of game narrative', no mention of personalization as a DV. Third, the **behavioural metrics** are unaware of being measured, so they cannot be demand-biased. Fourth, the interviewer was not me — my supervisor conducted six of the interviews to reduce my unconscious signalling. No mitigation is perfect, but these four combined make demand characteristics an unlikely explanation for the full pattern of results."

### Q: Is there a risk the LLM produces offensive content?

> "Yes. Phi-3.5 Mini has Microsoft's safety fine-tuning, but it's not bulletproof. Three mitigations. First, the prompt is heavily constrained — tone, length, topic. Second, the RAG context limits the generation to grounded lore. Third, a pre-display profanity filter runs on every generation; if it triggers, the narrative is dropped and replaced with a default. In 49 sessions we had zero observed offensive outputs, but I would not deploy this commercially without a human-in-the-loop review of the first few thousand generations. That's a deployment concern, not a research-phase concern."

---

## Category F — Ethics and SPER

### Q: You're profiling players. Isn't that surveillance?

> "Yes, it's behavioural surveillance. I don't pretend otherwise. Three mitigations make it defensible in this study. The data never leaves the device — SQLite is local, Ollama is local, there's no telemetry pipeline to a company server. No PII is collected beyond a session ID. And participants gave informed consent after being told their behaviour would be logged. For commercial deployment, I'd argue an adaptive game needs the same GDPR-grade opt-in that any behavioural analytics system needs — and I'd default to on-device-only processing, which this architecture already supports."

### Q: Flow-sustaining systems are manipulative. Is this ethical?

> "It's a mild form of psychological nudging, and I acknowledge it openly in Chapter 5. The ethical question is not whether it's manipulation — all entertainment design is some form of manipulation — but whether the manipulation serves the player. Flow, in Csikszentmihalyi's framework, is a state of engaged well-being. Nudging players toward Flow is nudging them toward an experience they generally endorse. That is *not* the same as nudging them toward addictive loops, lootbox spending, or session extension. The distinction is that this system optimises for a *player-endorsed* state, not a *publisher-endorsed* engagement metric. I would draw a sharp ethical line between the two."

### Q: Could this be used for predatory monetisation?

> "Yes. Any system that models player psychological state can be misused. A Flow classifier that identifies when a player is most engaged is exactly the signal a predatory publisher would use to time a lootbox prompt. I raise this explicitly in the SPER section. The mitigation is not technical — you can't design out the misuse potential — it's regulatory. I would support the same kind of disclosure requirements for adaptive systems that exist for lootboxes in some jurisdictions. This is in Chapter 5."

### Q: SPER approval date?

> "SPER form submitted and approved on the 14th of November 2025. Supervisor, Ms. Bimali Wickramasinghe, confirmed on the 21st of November. Copy is in Appendix E of the thesis."

---

## Category G — Future Work and Scaling

### Q: What would you do differently?

> "Three things. One: pre-register the study on OSF before data collection — I specified the analysis plan in SPER but not in a formal registration. Two: collect a Hexad questionnaire at the end of each session so I could validate the telemetry proxy against ground truth — that would have been fifteen extra minutes per participant, which I judged too costly at the time. Three: run a longer session, at least an hour, so cumulative narrative effects become measurable."

### Q: How would you validate Hexad proxies?

> "Concrete design. Recruit 100 players. Have them complete the 24-item Hexad questionnaire before playing. Then record thirty minutes of play and compute the telemetry-derived Hexad score. Compute Pearson correlations between the two, per dimension. A correlation above 0.5 per dimension would be a good validation; above 0.7 would be strong. If correlations are low for specific dimensions — I suspect Philanthropist, which is hardest to capture behaviourally — those proxies need redesigning. The study is in Chapter 6."

### Q: What's the path to a commercial game?

> "Three gates. First, scale — the backend needs session isolation, so multi-user state, session-keyed memory, likely a Redis cache in front of SQLite. Second, model quality — Phi-3.5 Mini is fine for a prototype; a commercial title needs either a fine-tuned 7B or a cloud-grade LLM with robust guardrails. Third, content pipeline — the lore corpus needs to be authorable by narrative designers, not hand-written by the programmer, which means a schema, a validator, and ideally an editor. The technical architecture is the easy part. The hard part is the content ops."

### Q: Could this be deployed to an existing game like Skyrim?

> "Technically, yes — the plugin is engine-agnostic at the boundary because it runs on telemetry events, not on Skyrim-internals. You'd need a mod that emits telemetry (there are Papyrus hooks for most of what I need), the Python backend unchanged, and a replacement for the HUD injector to render in Skyrim's UI. Practically: harder, because Skyrim's existing narrative would collide with injected narrative. You'd need rules to decide when the adaptive system talks and when vanilla dialogue takes over. That's a two-person-year integration, not a weekend."

---

## Category H — Curveballs

### Q: Why didn't you use GPT-4?

> "Cost and dependency. A thesis submission has to be reproducible by anyone who clones the repo. The moment I depend on a paid API, the reproducibility bar includes 'you must have an API key and money.' Phi-3.5 Mini via Ollama reproduces on any machine with 8GB of RAM, no account required. I also benchmarked the generations qualitatively against GPT-4 during pilot — GPT-4 is better prose, no question, but Phi-3.5 was good enough for the research question, which is whether adaptation works at all. Commercial deployment with a larger model is in Chapter 6."

### Q: If I said your work was trivial, what would you say?

> "I'd say: the individual techniques are not novel, and I never claim they are. What's novel is the specific composition — telemetry-derived Hexad plus Flow plus PPO plus RAG plus episodic memory running in a closed loop in a deployable Unity plugin. No prior system does this end-to-end. The empirical contribution is that this specific composition produces measurable effects on perceived personalization. Neither of those claims is trivial. If the panel disagrees, I'd want to hear which specific prior system they think already does this, and I'd argue the case on specifics."

### Q: What's the most surprising thing you learned?

> "The gap between self-report and behaviour — in the opposite direction from what I expected. I thought the Flow self-report would be the strongest signal, because it's the variable the system is optimising for. Instead, NPS-3 was the strongest by a wide margin, and the behavioural metrics — dialogue read ratio and voluntary NPC interactions — were *also* stronger than GEQ Flow. Players noticed the narrative change and responded to it behaviourally, but their self-reported Flow experience was more muted. That suggests narrative personalization might be perceived and acted on faster than it's *felt*. That's an interesting finding for the games UX literature."

### Q: If you had another six months, what would you do?

> "In order: one, run the Hexad validation study I described, because every downstream claim depends on those proxies. Two, swap the rule-based Flow classifier for a small LSTM trained on ESM-labelled Flow data, because the rule-based classifier is the weakest link in the pipeline. Three, scale the lore corpus tenfold and re-test, because thirty paragraphs is at the low end of what RAG can meaningfully differentiate. Four, run a multi-session longitudinal study. I'd accept that's more than six months of work; these would be in priority order."

### Q: What do you *not* know about this project?

> "Three things, honestly. One: I don't know how well the PPO policy generalises to players whose Hexad profile is outside the distribution I randomised during training — I didn't test edge cases like a pure Disruptor-only player. Two: I don't know how the narrative behaves over a multi-hour session; the longest test I ran was thirty-five minutes. Three: I don't have a rigorous answer for why Immersion didn't move — the mechanistic interpretation I gave on Slide 13 is plausible but not empirically proven. Those are the three places where my confidence is lowest."

---

## Recovery Strategies

**If you don't know:** say so clearly. "That's a good question — I don't have a precise answer for that. My best guess is *[reasoning]*, but I'd want to check *[source]* before committing to it." The panel is explicitly trained to penalise bluffing, not admission of uncertainty.

**If the question contains a wrong premise:** correct it gently before answering. "I think there may be a small miscommunication — my system actually does X, not Y. But to the spirit of the question: *[answer]*."

**If you need a moment:** say "Let me think about that for a second." A four-second pause is normal and preferable to a rushed wrong answer.

**If the panel pushes on a limitation:** concede, restate the limitation precisely, explain what you would do to fix it. Never defend against a limitation you've already acknowledged in writing.

**If a question is unclear:** ask for clarification. "Could I check — are you asking about *[X]* or *[Y]*?"

---

## Final Mental Model

The panel has already decided this is a competent project — they read the thesis. The viva is not about proving the work is good. It is about proving **you understand every decision you made**. When in doubt, optimise for *ownership* over *polish*. Say what you chose, why you chose it over alternatives, and what you would change with more time. That's what the Student Guidance literally asks for.