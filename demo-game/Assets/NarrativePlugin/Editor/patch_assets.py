"""
Patch AnyRPG FeaturesDemoGame assets to match the Eryndal narrative.
Sets displayName and description on scene nodes, factions, quests, unit profiles,
and rewrites dialog node lines.
Run from the repo root: python demo-game/Assets/NarrativePlugin/Editor/patch_assets.py
"""

import re
import os

BASE = "demo-game/Assets/AnyRPG/Core/Games/FeaturesDemoGame/Resources/FeaturesDemoGame"

# ── helpers ──────────────────────────────────────────────────────────────────

def read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write(path, content):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    print(f"  patched: {os.path.relpath(path)}")

def set_field(content, field, value):
    """Replace   field: <possibly multi-line value>  with   field: 'value'."""
    escaped = value.replace("'", "''")   # YAML single-quote escaping
    # Match the field plus any continuation lines (blank or indented deeper than 2 spaces),
    # stopping at the next same-level field or end of string.
    pattern = rf"  {re.escape(field)}:.*?(?=\n  \S|\Z)"
    replacement = f"  {field}: '{escaped}'"
    new = re.sub(pattern, replacement, content, count=1, flags=re.DOTALL)
    if new == content:
        print(f"    WARNING: field '{field}' not found")
    return new

def set_empty_field(content, field, value):
    """Only replace if the field is currently empty (displayName: )."""
    escaped = value.replace("'", "''")
    pattern = rf"(  {re.escape(field)}:)\s*$"
    replacement = rf"\1 '{escaped}'"
    new = re.sub(pattern, replacement, content, count=1, flags=re.MULTILINE)
    return new

def patch(rel_path, fields: dict):
    path = os.path.join(BASE, rel_path)
    c = read(path)
    for field, value in fields.items():
        c = set_empty_field(c, field, value) if field == "displayName" else set_field(c, field, value)
    write(path, c)

# ── scene nodes ───────────────────────────────────────────────────────────────

patch("SceneNode/FeaturesDemoZoneSceneNode.asset", {
    "displayName":  "The Contested Vale",
    "description":  "The frontline between the Azure Veil and the Crimson Host. Ruined outposts and open fields mark a war that neither side is winning.",
})
patch("SceneNode/FeaturesDemoDungeonSceneNode.asset", {
    "displayName":  "The Vault",
    "description":  "An ancient fortress buried beneath the Vale. Its lower chambers were sealed after the First Sundering. The seal is weakening.",
})
patch("SceneNode/FeaturesDemoCutsceneZoneSceneNode.asset", {
    "displayName":  "The Shattered Field",
    "description":  "An ancient battlefield from the First Sundering. Soldiers on both sides avoid it after dark.",
})

# ── factions ──────────────────────────────────────────────────────────────────

patch("Faction/BlueFaction.asset", {
    "displayName":  "Azure Veil",
    "description":  "A disciplined order fighting to hold ground and protect civilians. Losing ground is shameful; abandoning civilians is unforgivable.",
})
patch("Faction/RedFaction.asset", {
    "displayName":  "Crimson Host",
    "description":  "An aggressive force motivated by conquest. Archers, warriors, and necromancers who use any method that achieves victory.",
})
patch("Faction/EnemyFaction.asset", {
    "displayName":  "The Corrupted",
    "description":  "Creatures and soldiers corrupted by power leaking from the Vault's broken seal. They serve no living master and attack on sight.",
})

# ── quests ────────────────────────────────────────────────────────────────────

patch("Quest/KillThingsQuest.asset", {
    "displayName":  "Clear the Advance",
    "description":  "Push back the Crimson Host's forward units from the Vale's centre before they cut the Azure Veil's supply line.",
})
patch("Quest/CollectionQuest.asset", {
    "displayName":  "Salvage the Fallen",
    "description":  "Recover weapons and supplies from the battlefield before the Crimson Host finds them. Bring salvage to Sera at the supply post.",
})
patch("Quest/DialogObjectiveQuest.asset", {
    "displayName":  "Consult the Chronicler",
    "description":  "Speak with the Chronicler near the waystone. She knows whether the Vault can be entered safely.",
})
patch("Quest/VisitZoneQuest.asset", {
    "displayName":  "Descend to the Vault",
    "description":  "Scout the upper halls of the Vault and report back. Neither faction has committed forces underground yet.",
})
patch("Quest/RepeatableQuest.asset", {
    "displayName":  "Patrol Duty",
    "description":  "Complete your assigned patrol circuit across the Contested Vale.",
})
patch("Quest/Repeatable2StepQuest.asset", {
    "displayName":  "Patrol: Two Routes",
    "description":  "Complete two patrol checkpoints in the Contested Vale.",
})
patch("Quest/Repeatable3StepQuest.asset", {
    "displayName":  "Patrol: Three Routes",
    "description":  "Complete three patrol checkpoints across the Vale's contested sectors.",
})
patch("Quest/Repeatable5StepQuest.asset", {
    "displayName":  "Patrol: Full Circuit",
    "description":  "Complete the full five-checkpoint patrol circuit.",
})
patch("Quest/FinishAnotherQuestQuest.asset", {
    "displayName":  "Vault Clearance",
    "description":  "The upper Vault halls must be cleared of Vault Minions before the Azure Veil will commit to an assault on the sealed chamber.",
})
patch("Quest/ChooseRewardQuest.asset", {
    "displayName":  "Varis''s Favour",
    "description":  "Varis rewards soldiers who have proven themselves. Complete a series of tasks for the Azure Veil and choose your commendation.",
})
patch("Quest/StatusEffectQuest.asset", {
    "displayName":  "Combat Readiness: Status Effects",
    "description":  "Demonstrate you can apply a status effect in combat before Varis clears you for Vault assignment.",
})
patch("Quest/UseAbilityQuest.asset", {
    "displayName":  "Combat Readiness: Abilities",
    "description":  "Use the required abilities in combat. Varis does not send the untrained underground.",
})
patch("Quest/LearnAbilityQuest.asset", {
    "displayName":  "Training: New Abilities",
    "description":  "Learn the abilities required for Vault operations from the class trainers.",
})
patch("Quest/LearnTradeSkillQuest.asset", {
    "displayName":  "Trade Skills for the Front",
    "description":  "Acquire trade skills useful to the Azure Veil's war effort.",
})
patch("Quest/DialogIntroductionQuest.asset", {
    "displayName":  "Report to Varis",
    "description":  "Commander Varis at the Azure Veil's forward post has an urgent briefing for new arrivals in the Contested Vale.",
})
patch("Quest/UseInteractableQuest.asset", {
    "displayName":  "Activate the Waystone",
    "description":  "The Vale's ancient waystone may still function as a rally point. Locate and activate it.",
})

# ── unit profiles ─────────────────────────────────────────────────────────────

patch("UnitProfile/QuestNPCUnit.asset", {
    "displayName":  "Commander Varis",
    "description":  "Leader of the Azure Veil's forward post. Methodical and unsentimental. He rewards results, not effort.",
})
patch("UnitProfile/DialogNPCUnit.asset", {
    "displayName":  "The Chronicler",
    "description":  "A neutral scholar recording the war from near the waystone. She knows the history of the Vault and the First Sundering.",
})
patch("UnitProfile/VendorNPCUnit.asset", {
    "displayName":  "Sera",
    "description":  "Supplies trader at the Azure Veil's rear line. She has survived three faction occupations by being useful to whoever is in charge.",
})
patch("UnitProfile/BankNPCUnit.asset", {
    "displayName":  "Vault Keeper",
    "description":  "Manages the Azure Veil's secure storage at the forward post.",
})
patch("UnitProfile/EnemyBossUnit.asset", {
    "displayName":  "Vault Warden",
    "description":  "Once a soldier assigned to guard the sealed chamber. Corruption has left it barely recognisable. It defends the seal on instinct.",
})
patch("UnitProfile/EnemyMinionUnit.asset", {
    "displayName":  "Vault Minion",
    "description":  "Corrupted soldiers in various stages of decay. They retain enough instinct to flank and cut off retreats.",
})
patch("UnitProfile/DragonUnit.asset", {
    "displayName":  "The Bound One",
    "description":  "An ancient dragon sealed beneath the Vault's deepest chamber. Intelligent, patient, and not yet fully awake.",
})
patch("UnitProfile/CutsceneNPCUnit.asset", {
    "displayName":  "Fallen Knight",
    "description":  "A ghost-like vision of a knight from the First Sundering, seen in the Shattered Field.",
})

# ── dialogs ───────────────────────────────────────────────────────────────────
# Rewrites dialog node 'description' lines in place.

def patch_dialog(rel_path, nodes: list):
    """Replace dialogNodes descriptions. nodes = list of (description, nextOption) tuples."""
    path = os.path.join(BASE, rel_path)
    c = read(path)

    # Build new dialogNodes block
    lines_block = "  dialogNodes:\n"
    for desc, next_opt in nodes:
        d_escaped = desc.replace("'", "''")
        n_escaped = next_opt.replace("'", "''")
        lines_block += f"  - startTime: 0\n"
        lines_block += f"    showTime: 0\n"
        lines_block += f"    description: '{d_escaped}'\n"
        lines_block += f"    nextOption: {n_escaped}\n"

    # Replace existing dialogNodes block
    new_c = re.sub(
        r"  dialogNodes:.*?  prerequisiteConditions:",
        lines_block + "  prerequisiteConditions:",
        c,
        count=1,
        flags=re.DOTALL,
    )
    write(path, new_c)


def patch_speech_dialog(rel_path, nodes: list):
    """For speech bubble dialog with showTime values."""
    path = os.path.join(BASE, rel_path)
    c = read(path)
    lines_block = "  dialogNodes:\n"
    for show_time, desc in nodes:
        d_escaped = desc.replace("'", "''")
        lines_block += f"  - startTime: 0\n"
        lines_block += f"    showTime: {show_time}\n"
        lines_block += f"    description: '{d_escaped}'\n"
        lines_block += f"    nextOption: \n"
    new_c = re.sub(
        r"  dialogNodes:.*?  prerequisiteConditions:",
        lines_block + "  prerequisiteConditions:",
        c,
        count=1,
        flags=re.DOTALL,
    )
    write(path, new_c)


# The Chronicler — one-time briefing about the Vault (StandardDialog)
patch_dialog("Dialog/StandardDialog.asset", [
    ("The Vault has been sealed for thirty years. The seal was never meant to hold forever.", "What is inside it?"),
    ("Something that was not meant to be killed. Only delayed.", "The Bound One?"),
    ("That is one name for it. There are older names. I do not use them.", ""),
])

# Varis — repeatable patrol intel (RepeatableDialog)
patch_dialog("Dialog/RepeatableDialog.asset", [
    ("The Crimson Host pushed further north last night. Adjust your patrol route accordingly.", "How far north?"),
    ("Far enough that you should stop asking questions and start moving.", ""),
])

# Chronicler deeper lore — requires StandardDialog (PrerequisiteDialog)
patch_dialog("Dialog/PrerequisiteDialog.asset", [
    ("You want to know more about the First Sundering.", "I do."),
    ("This Vale is built on its aftermath. The factions are fighting over land that is already consecrated to the dead.", "Neither side knows?"),
    ("They know. They choose not to think about what that means.", ""),
])

# Ambient speech bubble — soldiers talking (SpeechBubbleDialog)
patch_speech_dialog("Dialog/SpeechBubbleDialog.asset", [
    (0,  "The Crimson Host moved their archers overnight. Watch the ridge."),
    (5,  "Vault Minions were spotted near the east entrance. Do not go in alone."),
])

# Quest intro dialog — Varis briefing (DialogIntroductionDialog)
patch_dialog("Dialog/DialogIntroductionDialog.asset", [
    ("You are late. The Crimson Host does not wait for stragglers.", ""),
    ("I am Commander Varis. You will receive your assignment now.", ""),
])

print("\nDone. Open Unity — assets will reimport automatically.")
