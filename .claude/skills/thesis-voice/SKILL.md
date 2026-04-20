---
name: thesis-voice
description: Writing style for this project's thesis and research paper. Use when drafting or editing any prose in docs/thesis/ or docs/reasearch-paper/ — LaTeX chapters, paper sections, abstracts, captions, rebuttal letters. Codifies the direct, explanatory voice established across ch1–ch6 of the thesis and the IEEE conference paper. Trigger whenever writing new content for or revising existing content in these documents.
allowed-tools: Read, Write, Edit, Glob, Grep
user-invocable: true
---

# Thesis Voice: Writing Style for the Dynamic Narrative Personalization Project

The thesis and accompanying research paper for this project use a specific voice: **direct, explanatory, concretely grounded, honest about limitations**. This skill codifies that voice so new prose drops into the documents without a register mismatch.

The goal is not "humanize AI text." The goal is to match *this specific author's established style* — the one already in place across [docs/thesis/chapters/](docs/thesis/chapters/) and [docs/reasearch-paper/main.tex](docs/reasearch-paper/main.tex). Readers should not be able to tell which paragraphs are new.

## When to use this skill

- Drafting or editing any chapter in [docs/thesis/chapters/](docs/thesis/chapters/)
- Writing or revising sections of [docs/reasearch-paper/main.tex](docs/reasearch-paper/main.tex)
- Composing abstracts, captions, reviewer responses, or supervisor-facing documents
- Updating Chapter 5 (Results) or Chapter 6 (Discussion) once user study data lands

Do **not** use for: code comments, commit messages, README files, backend docstrings, or Unity plugin documentation. Those have their own register.

---

## The Five Core Moves

### 1. Start with the concrete problem, not the abstract framing

**Anti-pattern** — abstract framing first:
> The domain of interactive narrative generation has long grappled with the challenge of authorial control. Numerous approaches have been proposed to address this challenge.

**Thesis voice** — put the problem bluntly:
> The central problem this research addresses is straightforward: current game narrative systems are static. They do not adapt their tone, urgency, or content to the psychological state and demonstrated preferences of an individual player in real time.

The thesis nearly always names the problem in its first or second sentence of any section. It does not warm up.

### 2. Explain with colon-expansions, not with subordination

The thesis uses colons heavily to expand a claim into its content, rather than burying the content in subordinate clauses.

**Anti-pattern**:
> Given that the cost of this mismatch is reduced engagement, which represents a missed opportunity to use narrative as a lever for nudging players back toward optimal experience, we argue that...

**Thesis voice**:
> The cost of this mismatch is twofold: reduced engagement in the short term, and a missed opportunity to use narrative as a lever for nudging players back toward optimal experience.

Pattern: `[Claim]: [item 1], [item 2].` Short setup, colon, content.

### 3. Use concrete imagery for abstract concepts

When introducing a concept, anchor it with a specific example the reader can picture.

**Anti-pattern**:
> The system responds differently depending on the player's current flow state, providing varied narrative adjustments.

**Thesis voice**:
> A player drifting into boredom, whose challenge--skill ratio has dropped below a meaningful threshold, continues to receive the same measured, low-stakes descriptions that a fully engaged player receives. A player overwhelmed by challenge, tipping into anxiety, gets no additional guidance from the narrative world.

The abstract idea (state-dependent narrative) is cashed out in scenes. Keep one concrete example per paragraph when introducing any mechanism.

### 4. Active voice and first-person-plural where it fits

The thesis uses "we" and active verbs. Passive voice appears only where the agent genuinely does not matter (e.g., method sections reporting procedure).

**Anti-pattern**:
> A Gymnasium-compatible MDP environment was constructed in which narrative adaptation is framed as a sequential decision problem.

**Thesis voice**:
> Construct a Gymnasium-compatible MDP environment that frames narrative adaptation as a sequential decision problem with a Flow-based reward signal.

### 5. Honest about limitations, without hedge-stacking

Limitations are named plainly, and the *reason* is given. The voice does not pile qualifiers; it states the constraint and moves on.

**Anti-pattern** — hedge stacking:
> It should be noted that there are a number of potential limitations that may possibly affect the generalizability of these results to some extent.

**Thesis voice**:
> The testbed is a 3D RPG built on the AnyRPG Core framework, not a commercially released title; this ensures experimental control but limits ecological validity.

Pattern: `[Constraint]; [what it buys you] but [what it costs you].` One sentence, both sides.

---

## Preferred Phrases (use freely when they fit)

These are turns of phrase the author has used repeatedly. They are not clichés in this document's register; they are established voice.

- "The concern is straightforward: …"
- "Put the problem bluntly, …"
- "The cost of this mismatch is twofold: …"
- "No system is stronger than its weakest assumption."
- "This makes sense as a chain: [step 1] → [step 2] → [step 3]."
- "[X] opens a design space that prior work has left unexplored."
- "[X] is a deliberate choice driven by [constraint]."
- "What has not appeared is a single [Y] that [does Z]."
- "The result is [concrete outcome]."
- "The gap is [X], not [Y]."

## Anti-Phrases (avoid)

These phrases have been specifically cut from the paper during style review. Do not reintroduce them.

- "operationalises X" → use "measures X via Y" or "treats X as Y in practice"
- "remains unquantified" → use "we do not have a number for this" or "no measurement exists"
- "shared variance is plausible" → use "these may be measuring the same thing"
- "fundamentally reshapes our understanding"
- "a pivotal / crucial / vital contribution"
- "multifaceted", "intricate interplay", "tapestry", "landscape" (metaphorical), "delve into"
- "Drawing on [theorist]'s framework, …"
- "It is widely accepted that …"
- "Future research should explore …" (unless followed by a specific prediction)
- "This has important implications for policy and practice"

## Em-dash policy

The paper refinement pass explicitly removed `---` (em-dashes) in favour of parentheses or semicolons. **Use em-dashes sparingly — ideally fewer than three per page of LaTeX.** When you reach for one, first ask whether parentheses, a semicolon, or a sentence break would work.

- `---` for parenthetical aside → use `(like this)` or `, like this,`
- `---` for strong separator → use `;`
- `---` for emphasis/pivot → use a new sentence

One or two em-dashes in a chapter is fine. A paragraph with three is a signal to rewrite.

---

## Statistical Reporting Rules

The thesis and paper report statistics *honestly*. This is a non-negotiable part of the voice.

1. **Flag non-significant results explicitly.** If `p > .05` after correction, say so in the same sentence as the effect size. Never let a `d = 0.65` stand alone without context.
2. **Always include 95% CIs alongside point estimates.** `d = 0.84, 95% CI [0.23, 1.45]`.
3. **Apply and report corrections.** Bonferroni, Holm, whichever — name it and give the adjusted alpha.
4. **Check and state the assumption used.** "Shapiro-Wilk suggested non-normality in the Flow subscale; we report Welch's *t* and a Mann-Whitney U confirmation."
5. **Acknowledge shared variance between related measures.** The NPS-3 and GEQ Flow likely overlap; say so when reporting both.
6. **Never present unrun results as real.** If the study has not been conducted, results must be flagged as projected, hypothetical, or simulated. The current paper still has this problem — when updating it post-study, either replace with real data or add explicit hypothetical framing.

## Section opening rhythm

Sections in this thesis tend to open with a one-sentence frame, then expand. They do not open with a definition dump.

**Good opener**:
> The aim of this research is to show that a closed-loop, AI-driven narrative personalization system, packaged as a game-engine plugin, can measurably improve player experience when compared with static narrative delivery.

**Bad opener** (definition dump):
> Personalization in interactive media refers to the tailoring of content to individual users. This concept has been studied extensively in various domains including e-commerce, education, and entertainment.

---

## Side-by-side Transformations (from the actual refinement pass)

These are real before/after pairs from the style edits applied to [docs/reasearch-paper/main.tex](docs/reasearch-paper/main.tex). Use them as calibration.

**1. Abstract clinical → direct**

Before:
> This work operationalises Csikszentmihalyi's challenge-skill balance axis through a rule-based Flow classifier and uses a PPO policy to select among eight narrative modulation actions.

After:
> We detect Flow state with a rule-based classifier built on Csikszentmihalyi's challenge–skill balance, then use a PPO policy to pick among eight narrative modulation actions.

**2. Passive + nominalisation → active**

Before:
> A reduction in the number of cold-start events was observed following the introduction of the heuristic mapping.

After:
> The heuristic mapping cut cold-start events roughly in half during the first two minutes of a session.

**3. Hedge stack → single honest sentence**

Before:
> It may possibly be the case that the NPS-3 instrument could be measuring, at least in part, something that overlaps with the GEQ Flow subscale.

After:
> The NPS-3 and GEQ Flow subscale probably share variance; we cannot cleanly separate "perceived personalization" from "felt immersion" with these two instruments alone.

**4. Generic significance → concrete claim**

Before:
> This research makes a significant contribution to the field of AI-driven game narrative.

After:
> What has not appeared before is a single deployable Unity plugin that wires player modelling, RL adaptation, RAG-grounded LLM generation, and episodic memory into one closed loop. This work delivers that plugin.

---

## The viva-defensibility filter

Before committing any claim in the thesis or paper, ask: **could I defend this sentence in a viva without flinching?**

- If yes → keep it.
- If "probably, depending on how they ask" → soften or cite.
- If "only if they don't push" → rewrite or cut.

This is the single most important filter during Results/Discussion writing.

---

## Workflow

When asked to draft or edit thesis/paper content:

1. **Read the target file** to confirm it lives in [docs/thesis/](docs/thesis/) or [docs/reasearch-paper/](docs/reasearch-paper/)
2. **Read the surrounding section** to pick up local terminology and references
3. **Draft in this voice** — start concrete, colon-expand, active verbs, name limitations plainly
4. **Self-audit against the anti-phrase list** before proposing the edit
5. **Check em-dash count** — if more than ~2 in a paragraph, rewrite
6. **Use Edit tool, not Write** — these files exist; make targeted changes
7. **Never introduce unrun results as real** — if inventing data for a placeholder, mark it clearly

## Quick checklist for any new paragraph

- [ ] First sentence names the concrete thing, not the abstract framing
- [ ] At least one specific example or image
- [ ] Active verbs; passive only where the agent doesn't matter
- [ ] Limitations (if any) stated in one sentence with trade-off named
- [ ] No anti-phrases from the list above
- [ ] Em-dashes under two per paragraph
- [ ] If reporting stats: effect size + CI + significance status + correction named
- [ ] Could defend every sentence in a viva

If all boxes check, the paragraph is in voice.