# Dynamic Narrative Personalization Plugin — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a closed-loop Unity plugin that personalizes RPG narrative in real-time using a hybrid player model, RAG-grounded LLM narrative generation, and PPO reinforcement learning driven by Flow theory rewards.

**Architecture:** Five-module pipeline — Player Data Logger (Unity) → Player Modeling Service (Python/ML) → Narrative Generation Service (Python/Ollama+ChromaDB) → Adaptation Engine (Python/SB3-PPO) → Content Injection Module (Unity). All components communicate via FastAPI (WebSocket for telemetry, REST for narrative). The player profile uses a Hexad-inspired 6-dimensional continuous vector derived from a Transformer-based session embedding (player2vec approach), not static Bartle types.

**Tech Stack:** Unity 6 LTS · Python 3.12 · FastAPI · Ollama (Phi-3.5 Mini 3.8B or Llama 3.2 3B) · ChromaDB · Stable-Baselines3 (PPO) · scikit-learn / XGBoost · SQLite · sentence-transformers

---

## Repo Structure

```
fyp-v2/
├── backend/
│   ├── main.py                        # FastAPI entrypoint
│   ├── config.py                      # Pydantic settings
│   ├── models/                        # Pydantic schemas
│   │   ├── telemetry.py
│   │   ├── player_model.py
│   │   └── narrative.py
│   ├── player_modeling/
│   │   ├── state_classifier.py        # Rule-based CurrentState
│   │   ├── feature_extractor.py       # Telemetry → feature vector
│   │   ├── flow_classifier.py         # XGBoost Flow state
│   │   └── session_embedder.py        # Transformer session embedding
│   ├── narrative/
│   │   ├── prompt_builder.py          # Dynamic prompt construction
│   │   ├── ollama_client.py           # LLM interface
│   │   ├── rag_retriever.py           # ChromaDB lore retrieval
│   │   └── memory.py                  # Episodic session memory
│   ├── adaptation/
│   │   ├── rl_env.py                  # Gym environment (MDP)
│   │   ├── reward.py                  # Reward function
│   │   └── agent.py                   # PPO agent wrapper
│   ├── db/
│   │   └── telemetry_store.py         # SQLite logging
│   └── tests/
│       ├── test_player_modeling.py
│       ├── test_narrative.py
│       ├── test_rl_env.py
│       └── test_api.py
├── unity-plugin/
│   ├── Runtime/
│   │   ├── PlayerDataLogger.cs
│   │   ├── NarrativeManager.cs
│   │   ├── ContentInjector.cs
│   │   └── PluginConfig.cs            # ScriptableObject
│   └── Tests/
│       └── EditMode/
│           └── TelemetryBatchTests.cs
├── testbed-game/                      # Unity 6 project (2D top-down RPG)
│   └── Assets/
│       ├── Scripts/
│       │   ├── GameManager.cs
│       │   ├── CombatSystem.cs
│       │   ├── NPCDialogueController.cs
│       │   └── TelemetryHooks.cs
│       └── ScriptableObjects/
│           └── PluginConfig.asset
├── lore/                              # Game lore documents for RAG
│   ├── world.md
│   ├── characters.md
│   └── quests.md
├── data/
│   └── telemetry.db                   # SQLite (auto-created)
├── notebooks/
│   └── rl_training.ipynb             # PPO training notebook
├── docs/
│   └── plans/
│       └── 2026-02-27-dynamic-narrative-personalization.md
├── requirements.txt
└── README.md
```

---

## Task 1: Project Scaffold & Backend Foundation

**Files:**
- Create: `backend/main.py`
- Create: `backend/config.py`
- Create: `backend/models/telemetry.py`
- Create: `backend/models/player_model.py`
- Create: `backend/models/narrative.py`
- Create: `requirements.txt`

**Step 1: Write the failing test**
```python
# backend/tests/test_api.py
from fastapi.testclient import TestClient
from backend.main import app

def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

**Step 2: Run to verify it fails**
```bash
cd backend && pytest tests/test_api.py::test_health_endpoint -v
# Expected: FAIL — ImportError or 404
```

**Step 3: Implement**
```python
# backend/main.py
from fastapi import FastAPI
from backend.routers import telemetry, narrative

app = FastAPI(title="Narrative Personalization API", version="0.1.0")
app.include_router(telemetry.router, prefix="/ws")
app.include_router(narrative.router, prefix="/api")

@app.get("/health")
async def health(): return {"status": "ok"}
```

```python
# backend/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "phi3.5"          # or "llama3.2:3b"
    chroma_persist_dir: str = "./data/chroma"
    sqlite_path: str = "./data/telemetry.db"
    telemetry_window_seconds: int = 5
    flow_cold_start_seconds: int = 120

settings = Settings()
```

```python
# backend/models/telemetry.py
from pydantic import BaseModel
from typing import Optional

class TelemetryBatch(BaseModel):
    player_id: str
    session_id: str
    window_start: float          # Unix timestamp
    window_end: float
    kills: int = 0
    deaths: int = 0
    damage_taken: float = 0.0
    damage_dealt: float = 0.0
    abilities_used: int = 0
    abilities_hit: int = 0
    objectives_completed: int = 0
    objectives_attempted: int = 0
    tiles_explored: int = 0
    total_tiles: int = 100
    npc_interactions_voluntary: int = 0
    dialogue_lines_shown: int = 0
    dialogue_lines_skipped: int = 0
    lore_items_read: int = 0
    lore_items_found: int = 0
    idle_seconds: float = 0.0
    session_elapsed: float = 0.0
    current_location: str = "unknown"
    current_objective: str = "none"
```

```python
# backend/models/player_model.py
from pydantic import BaseModel
from enum import Enum

class FlowState(str, Enum):
    FLOW = "FLOW"
    ANXIETY = "ANXIETY"
    BOREDOM = "BOREDOM"
    APATHY = "APATHY"

class CurrentState(str, Enum):
    IN_COMBAT = "IN_COMBAT"
    EXPLORING = "EXPLORING"
    IN_DIALOGUE = "IN_DIALOGUE"
    IDLE = "IDLE"

class HexadProfile(BaseModel):
    achiever: float = 0.5       # Goal/completion oriented
    explorer: float = 0.5       # Discovery/lore oriented
    socializer: float = 0.5     # NPC/story interaction
    free_spirit: float = 0.5    # Open-world, off-path
    disruptor: float = 0.5      # Combat, chaos preference
    philanthropist: float = 0.5 # Helping/altruistic choices

class PlayerModel(BaseModel):
    player_id: str
    session_id: str
    timestamp: float
    current_state: CurrentState
    flow_state: FlowState
    flow_score: float            # 0.0-1.0 confidence
    challenge_skill_ratio: float # <0.8 easy, 0.8-1.2 flow, >1.2 hard
    hexad_profile: HexadProfile
    session_embedding: list[float] = []  # 64-dim from Transformer
    session_elapsed: float = 0.0
```

```python
# backend/models/narrative.py
from pydantic import BaseModel
from enum import Enum
from typing import Optional

class NarrativeAction(str, Enum):
    LOWER_STAKES = "LOWER_STAKES"
    RAISE_STAKES = "RAISE_STAKES"
    ADD_MYSTERY = "ADD_MYSTERY"
    ADD_HUMOR = "ADD_HUMOR"
    PROVIDE_GUIDANCE = "PROVIDE_GUIDANCE"
    INCREASE_URGENCY = "INCREASE_URGENCY"
    LORE_REWARD = "LORE_REWARD"
    NO_CHANGE = "NO_CHANGE"

class NarrativeContentType(str, Enum):
    DIALOGUE = "dialogue"
    DESCRIPTION = "description"
    QUEST_UPDATE = "quest_update"

class NarrativeContent(BaseModel):
    action_taken: NarrativeAction
    content_type: NarrativeContentType
    content: str
    speaker: Optional[str] = None
    emotional_tone: str = "neutral"
    lore_refs: list[str] = []        # RAG source references
    fallback: bool = False
```

```
# requirements.txt
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
pydantic>=2.10.0
pydantic-settings>=2.7.0
websockets>=14.0
httpx>=0.28.0
stable-baselines3>=2.4.0
gymnasium>=1.0.0
scikit-learn>=1.6.0
xgboost>=2.1.0
chromadb>=0.6.0
sentence-transformers>=3.3.0
sqlalchemy>=2.0.0
numpy>=2.0.0
pytest>=8.3.0
pytest-asyncio>=0.24.0
httpx>=0.28.0
```

**Step 4: Run test to verify it passes**
```bash
pytest tests/test_api.py::test_health_endpoint -v
# Expected: PASS
```

**Step 5: Commit**
```bash
git add backend/ requirements.txt
git commit -m "feat: scaffold FastAPI backend with schema models"
```

---

## Task 2: SQLite Telemetry Storage

**Files:**
- Create: `backend/db/telemetry_store.py`
- Test: `backend/tests/test_api.py` (extend)

**Step 1: Write failing tests**
```python
# backend/tests/test_api.py (add)
from backend.db.telemetry_store import TelemetryStore
from backend.models.telemetry import TelemetryBatch
import time

def test_store_and_retrieve_telemetry():
    store = TelemetryStore(":memory:")
    batch = TelemetryBatch(
        player_id="p1", session_id="s1",
        window_start=time.time()-5, window_end=time.time(),
        kills=3, deaths=1
    )
    store.insert(batch)
    rows = store.get_session("s1")
    assert len(rows) == 1
    assert rows[0].kills == 3

def test_get_last_n_batches():
    store = TelemetryStore(":memory:")
    for i in range(5):
        batch = TelemetryBatch(
            player_id="p1", session_id="s1",
            window_start=float(i*5), window_end=float((i+1)*5),
            kills=i
        )
        store.insert(batch)
    recent = store.get_last_n("s1", n=3)
    assert len(recent) == 3
    assert recent[-1].kills == 4   # most recent
```

**Step 2: Run to verify fails**
```bash
pytest tests/test_api.py::test_store_and_retrieve_telemetry -v
# Expected: FAIL — ImportError
```

**Step 3: Implement**
```python
# backend/db/telemetry_store.py
import sqlite3
import json
from backend.models.telemetry import TelemetryBatch

class TelemetryStore:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_table()

    def _create_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                window_start REAL,
                window_end REAL,
                data JSON NOT NULL
            )
        """)
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_session ON telemetry(session_id)")
        self.conn.commit()

    def insert(self, batch: TelemetryBatch):
        self.conn.execute(
            "INSERT INTO telemetry (player_id, session_id, window_start, window_end, data) VALUES (?,?,?,?,?)",
            (batch.player_id, batch.session_id,
             batch.window_start, batch.window_end,
             batch.model_dump_json())
        )
        self.conn.commit()

    def get_session(self, session_id: str) -> list[TelemetryBatch]:
        rows = self.conn.execute(
            "SELECT data FROM telemetry WHERE session_id=? ORDER BY window_start ASC",
            (session_id,)
        ).fetchall()
        return [TelemetryBatch.model_validate_json(r[0]) for r in rows]

    def get_last_n(self, session_id: str, n: int = 10) -> list[TelemetryBatch]:
        rows = self.conn.execute(
            "SELECT data FROM telemetry WHERE session_id=? ORDER BY window_start DESC LIMIT ?",
            (session_id, n)
        ).fetchall()
        return [TelemetryBatch.model_validate_json(r[0]) for r in rows][::-1]
```

**Step 4: Run to verify passes**
```bash
pytest tests/test_api.py -v
# Expected: all PASS
```

**Step 5: Commit**
```bash
git add backend/db/ backend/tests/
git commit -m "feat: SQLite telemetry storage with session queries"
```

---

## Task 3: WebSocket Telemetry Endpoint

**Files:**
- Create: `backend/routers/telemetry.py`
- Test: `backend/tests/test_api.py` (extend)

**Step 1: Write failing test**
```python
# backend/tests/test_api.py (add)
from fastapi.testclient import TestClient
import json, time

def test_websocket_telemetry_accepted():
    client = TestClient(app)
    with client.websocket_connect("/ws/telemetry") as ws:
        batch = {
            "player_id": "p1", "session_id": "s1",
            "window_start": time.time()-5, "window_end": time.time(),
            "kills": 2, "deaths": 0
        }
        ws.send_json(batch)
        response = ws.receive_json()
        assert response["status"] == "received"

def test_websocket_invalid_payload_returns_error():
    client = TestClient(app)
    with client.websocket_connect("/ws/telemetry") as ws:
        ws.send_json({"bad": "data"})
        response = ws.receive_json()
        assert response["status"] == "error"
```

**Step 2: Run to verify fails**
```bash
pytest tests/test_api.py::test_websocket_telemetry_accepted -v
# Expected: FAIL
```

**Step 3: Implement**
```python
# backend/routers/telemetry.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError
from backend.models.telemetry import TelemetryBatch
from backend.db.telemetry_store import TelemetryStore
from backend.config import settings

router = APIRouter()
_store = TelemetryStore(settings.sqlite_path)

@router.websocket("/telemetry")
async def telemetry_ws(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            try:
                batch = TelemetryBatch(**data)
                _store.insert(batch)
                await websocket.send_json({"status": "received", "session_id": batch.session_id})
            except (ValidationError, Exception) as e:
                await websocket.send_json({"status": "error", "detail": str(e)})
    except WebSocketDisconnect:
        pass
```

**Step 4: Run to verify passes**
```bash
pytest tests/test_api.py -v
# Expected: all PASS
```

**Step 5: Commit**
```bash
git add backend/routers/
git commit -m "feat: WebSocket telemetry endpoint with validation"
```

---

## Task 4: Feature Extraction & Flow State Classifier

**Files:**
- Create: `backend/player_modeling/feature_extractor.py`
- Create: `backend/player_modeling/flow_classifier.py`
- Test: `backend/tests/test_player_modeling.py`

**Step 1: Write failing tests**
```python
# backend/tests/test_player_modeling.py
from backend.player_modeling.feature_extractor import FeatureExtractor
from backend.player_modeling.flow_classifier import FlowClassifier
from backend.models.telemetry import TelemetryBatch
from backend.models.player_model import FlowState
import time

def _make_batch(kills=3, deaths=1, damage_taken=50.0,
                objectives_completed=2, objectives_attempted=3) -> TelemetryBatch:
    return TelemetryBatch(
        player_id="p1", session_id="s1",
        window_start=time.time()-5, window_end=time.time(),
        kills=kills, deaths=deaths,
        damage_taken=damage_taken,
        objectives_completed=objectives_completed,
        objectives_attempted=objectives_attempted,
        tiles_explored=40, total_tiles=100,
        dialogue_lines_shown=10, dialogue_lines_skipped=2,
        session_elapsed=300
    )

def test_feature_extractor_returns_expected_keys():
    extractor = FeatureExtractor()
    features = extractor.extract([_make_batch()])
    expected_keys = {"kd_ratio", "objective_rate", "explore_rate",
                     "dialogue_engage_rate", "damage_taken_norm",
                     "idle_ratio", "challenge_skill_ratio"}
    assert expected_keys.issubset(features.keys())

def test_challenge_skill_ratio_high_death_increases_ratio():
    extractor = FeatureExtractor()
    easy = extractor.extract([_make_batch(kills=10, deaths=0, damage_taken=5.0)])
    hard = extractor.extract([_make_batch(kills=0, deaths=5, damage_taken=200.0)])
    assert hard["challenge_skill_ratio"] > easy["challenge_skill_ratio"]

def test_flow_classifier_returns_valid_state():
    classifier = FlowClassifier()
    extractor = FeatureExtractor()
    features = extractor.extract([_make_batch()])
    state, confidence = classifier.classify(features)
    assert state in [s.value for s in FlowState]
    assert 0.0 <= confidence <= 1.0

def test_flow_classifier_boredom_on_easy_play():
    classifier = FlowClassifier()
    extractor = FeatureExtractor()
    # Very easy play: high kills, 0 deaths, low damage
    features = extractor.extract([
        _make_batch(kills=20, deaths=0, damage_taken=0.0,
                    objectives_completed=5, objectives_attempted=5)
    ])
    state, _ = classifier.classify(features)
    assert state == FlowState.BOREDOM

def test_flow_classifier_anxiety_on_hard_play():
    classifier = FlowClassifier()
    extractor = FeatureExtractor()
    features = extractor.extract([
        _make_batch(kills=0, deaths=8, damage_taken=500.0,
                    objectives_completed=0, objectives_attempted=5)
    ])
    state, _ = classifier.classify(features)
    assert state == FlowState.ANXIETY
```

**Step 2: Run to verify fails**
```bash
pytest tests/test_player_modeling.py -v
# Expected: all FAIL
```

**Step 3: Implement feature extractor**
```python
# backend/player_modeling/feature_extractor.py
from backend.models.telemetry import TelemetryBatch
import numpy as np

class FeatureExtractor:
    """
    Extracts normalized features from a window of telemetry batches.
    All features are in [0,1] range. challenge_skill_ratio is unbounded but clipped to [0,3].
    """

    def extract(self, batches: list[TelemetryBatch]) -> dict[str, float]:
        if not batches:
            return self._default_features()

        kills = sum(b.kills for b in batches)
        deaths = max(sum(b.deaths for b in batches), 1)  # avoid div0
        damage_taken = sum(b.damage_taken for b in batches)
        objectives_completed = sum(b.objectives_completed for b in batches)
        objectives_attempted = max(sum(b.objectives_attempted for b in batches), 1)
        tiles_explored = max(b.tiles_explored for b in batches)
        total_tiles = batches[-1].total_tiles
        dialogue_shown = max(sum(b.dialogue_lines_shown for b in batches), 1)
        dialogue_skipped = sum(b.dialogue_lines_skipped for b in batches)
        idle_seconds = sum(b.idle_seconds for b in batches)
        session_elapsed = max(batches[-1].session_elapsed, 1.0)
        lore_read = sum(b.lore_items_read for b in batches)
        lore_found = max(sum(b.lore_items_found for b in batches), 1)
        abilities_hit = sum(b.abilities_hit for b in batches)
        abilities_used = max(sum(b.abilities_used for b in batches), 1)

        kd_ratio = min(kills / deaths, 5.0) / 5.0           # normalize to [0,1]
        objective_rate = objectives_completed / objectives_attempted
        explore_rate = min(tiles_explored / total_tiles, 1.0)
        dialogue_engage_rate = 1.0 - (dialogue_skipped / dialogue_shown)
        ability_accuracy = abilities_hit / abilities_used
        damage_taken_norm = min(damage_taken / (session_elapsed / 60.0 + 1), 200) / 200
        idle_ratio = min(idle_seconds / session_elapsed, 1.0)
        lore_engage_rate = lore_read / lore_found

        # skill_score: high kd, high objective, high accuracy, low idle
        skill_score = (0.35*kd_ratio + 0.30*objective_rate +
                       0.20*ability_accuracy + 0.15*(1-idle_ratio))

        # challenge_score: high damage, low objective rate
        challenge_score = (0.50*damage_taken_norm +
                           0.30*(1-objective_rate) +
                           0.20*(deaths / (deaths + kills + 1)))

        ratio = float(np.clip(challenge_score / max(skill_score, 0.001), 0.0, 3.0))

        return {
            "kd_ratio": kd_ratio,
            "objective_rate": objective_rate,
            "explore_rate": explore_rate,
            "dialogue_engage_rate": dialogue_engage_rate,
            "ability_accuracy": ability_accuracy,
            "damage_taken_norm": damage_taken_norm,
            "idle_ratio": idle_ratio,
            "lore_engage_rate": lore_engage_rate,
            "skill_score": skill_score,
            "challenge_score": challenge_score,
            "challenge_skill_ratio": ratio,
        }

    def _default_features(self) -> dict[str, float]:
        return {k: 0.5 for k in [
            "kd_ratio","objective_rate","explore_rate","dialogue_engage_rate",
            "ability_accuracy","damage_taken_norm","idle_ratio","lore_engage_rate",
            "skill_score","challenge_score","challenge_skill_ratio"
        ]}
```

```python
# backend/player_modeling/flow_classifier.py
from backend.models.player_model import FlowState

class FlowClassifier:
    """
    Rule-based Flow state classification from challenge_skill_ratio.
    Thresholds derived from Csikszentmihalyi (1990) and empirical
    game research (42.4% Flow, 28.4% Boredom, 20.7% Anxiety — PMC 2022).

    Future work: replace with XGBoost trained on labeled session data.
    """
    BOREDOM_THRESHOLD = 0.75    # ratio < 0.75 → too easy → BOREDOM
    ANXIETY_THRESHOLD = 1.30    # ratio > 1.30 → too hard → ANXIETY
    APATHY_IDLE_THRESHOLD = 0.4 # idle_ratio > 0.4 AND low engagement → APATHY

    def classify(self, features: dict[str, float]) -> tuple[FlowState, float]:
        ratio = features["challenge_skill_ratio"]
        idle = features["idle_ratio"]
        dialogue_engage = features["dialogue_engage_rate"]

        # Apathy: low engagement across all dimensions
        if idle > self.APATHY_IDLE_THRESHOLD and dialogue_engage < 0.3 and ratio < 0.6:
            return FlowState.APATHY, 0.70

        if ratio < self.BOREDOM_THRESHOLD:
            # Confidence scales with distance from threshold
            conf = min(1.0, 0.6 + (self.BOREDOM_THRESHOLD - ratio) * 0.8)
            return FlowState.BOREDOM, conf

        if ratio > self.ANXIETY_THRESHOLD:
            conf = min(1.0, 0.6 + (ratio - self.ANXIETY_THRESHOLD) * 0.4)
            return FlowState.ANXIETY, conf

        # In the channel
        # Higher confidence when ratio is close to 1.0 (perfect balance)
        distance_from_ideal = abs(ratio - 1.0)
        conf = max(0.55, 1.0 - distance_from_ideal * 1.2)
        return FlowState.FLOW, conf
```

**Step 4: Run to verify passes**
```bash
pytest tests/test_player_modeling.py -v
# Expected: all PASS
```

**Step 5: Commit**
```bash
git add backend/player_modeling/ backend/tests/test_player_modeling.py
git commit -m "feat: feature extraction and rule-based Flow state classifier"
```

---

## Task 5: Hexad Playstyle Profiler

**Files:**
- Create: `backend/player_modeling/hexad_profiler.py`
- Test: `backend/tests/test_player_modeling.py` (extend)

**Step 1: Write failing tests**
```python
# backend/tests/test_player_modeling.py (add)
from backend.player_modeling.hexad_profiler import HexadProfiler
from backend.models.player_model import HexadProfile

def test_hexad_profiler_explorer_high_on_exploration():
    profiler = HexadProfiler()
    history = [
        _make_batch(kills=1, deaths=0),
        TelemetryBatch(
            player_id="p1", session_id="s1",
            window_start=0, window_end=5,
            tiles_explored=80, total_tiles=100,
            lore_items_read=5, lore_items_found=5,
            npc_interactions_voluntary=3,
            session_elapsed=300
        )
    ]
    profile = profiler.compute(history)
    assert profile.explorer > 0.6
    assert isinstance(profile, HexadProfile)

def test_hexad_profiler_disruptor_high_on_combat():
    profiler = HexadProfiler()
    history = [_make_batch(kills=15, deaths=2, damage_dealt=800.0)]
    profile = profiler.compute(history)
    assert profile.disruptor > 0.6
```

**Step 2: Run to verify fails**
```bash
pytest tests/test_player_modeling.py::test_hexad_profiler_explorer_high_on_exploration -v
```

**Step 3: Implement**
```python
# backend/player_modeling/hexad_profiler.py
"""
Maps player telemetry to Hexad player type dimensions (Tondello et al., 2016).
Hexad types grounded in Self-Determination Theory — more nuanced than Bartle.
Each dimension in [0,1]; derived from rolling session telemetry.
"""
from backend.models.player_model import HexadProfile
from backend.models.telemetry import TelemetryBatch
import numpy as np

class HexadProfiler:
    def compute(self, batches: list[TelemetryBatch]) -> HexadProfile:
        if not batches:
            return HexadProfile()

        # Aggregate raw signals
        kills = sum(b.kills for b in batches)
        deaths = sum(b.deaths for b in batches)
        tiles_explored = max(b.tiles_explored for b in batches)
        total_tiles = batches[-1].total_tiles
        lore_read = sum(b.lore_items_read for b in batches)
        lore_found = max(sum(b.lore_items_found for b in batches), 1)
        voluntary_npc = sum(b.npc_interactions_voluntary for b in batches)
        obj_completed = sum(b.objectives_completed for b in batches)
        obj_attempted = max(sum(b.objectives_attempted for b in batches), 1)
        dialogue_engage = 1 - (sum(b.dialogue_lines_skipped for b in batches) /
                               max(sum(b.dialogue_lines_shown for b in batches), 1))

        def norm(x, max_val): return float(np.clip(x / max_val, 0.0, 1.0))

        # Hexad dimension mappings:
        achiever     = 0.7 * (obj_completed/obj_attempted) + 0.3 * norm(kills, 20)
        explorer     = 0.5 * norm(tiles_explored, total_tiles) + 0.5 * (lore_read/lore_found)
        socializer   = 0.6 * norm(voluntary_npc, 10) + 0.4 * dialogue_engage
        free_spirit  = 0.5 * norm(tiles_explored, total_tiles) + 0.5 * (1 - obj_completed/obj_attempted)
        disruptor    = 0.7 * norm(kills, 20) + 0.3 * norm(deaths, 10)
        philanthropist = 0.6 * dialogue_engage + 0.4 * (lore_read/lore_found)

        return HexadProfile(
            achiever=round(float(np.clip(achiever, 0, 1)), 3),
            explorer=round(float(np.clip(explorer, 0, 1)), 3),
            socializer=round(float(np.clip(socializer, 0, 1)), 3),
            free_spirit=round(float(np.clip(free_spirit, 0, 1)), 3),
            disruptor=round(float(np.clip(disruptor, 0, 1)), 3),
            philanthropist=round(float(np.clip(philanthropist, 0, 1)), 3),
        )
```

**Step 4: Run to verify passes**
```bash
pytest tests/test_player_modeling.py -v
```

**Step 5: Commit**
```bash
git add backend/player_modeling/hexad_profiler.py
git commit -m "feat: Hexad-based continuous playstyle profiler"
```

---

## Task 6: Player Modeling REST Endpoint

**Files:**
- Create: `backend/player_modeling/modeling_service.py`
- Create: `backend/routers/player_model.py`
- Test: `backend/tests/test_api.py` (extend)

**Step 1: Write failing test**
```python
# backend/tests/test_api.py (add)
import time

def test_player_model_endpoint_returns_valid_model():
    client = TestClient(app)
    # First insert some telemetry
    with client.websocket_connect("/ws/telemetry") as ws:
        ws.send_json({
            "player_id": "p1", "session_id": "test-session",
            "window_start": time.time()-5, "window_end": time.time(),
            "kills": 5, "deaths": 1, "damage_taken": 80.0,
            "objectives_completed": 2, "objectives_attempted": 3,
            "tiles_explored": 30, "total_tiles": 100,
            "session_elapsed": 300
        })
        ws.receive_json()

    response = client.get("/api/player-model/test-session")
    assert response.status_code == 200
    model = response.json()
    assert "flow_state" in model
    assert model["flow_state"] in ["FLOW", "ANXIETY", "BOREDOM", "APATHY"]
    assert "hexad_profile" in model
```

**Step 2: Run to verify fails**
```bash
pytest tests/test_api.py::test_player_model_endpoint_returns_valid_model -v
```

**Step 3: Implement**
```python
# backend/player_modeling/modeling_service.py
from backend.db.telemetry_store import TelemetryStore
from backend.player_modeling.feature_extractor import FeatureExtractor
from backend.player_modeling.flow_classifier import FlowClassifier
from backend.player_modeling.hexad_profiler import HexadProfiler
from backend.models.player_model import PlayerModel, CurrentState
from backend.config import settings
import time

class PlayerModelingService:
    def __init__(self, store: TelemetryStore):
        self.store = store
        self.extractor = FeatureExtractor()
        self.flow_clf = FlowClassifier()
        self.hexad = HexadProfiler()

    def get_model(self, session_id: str, player_id: str = "unknown") -> PlayerModel:
        # Use last 3 windows (15-second rolling window)
        batches = self.store.get_last_n(session_id, n=3)
        if not batches:
            return self._default_model(player_id, session_id)

        features = self.extractor.extract(batches)
        flow_state, flow_score = self.flow_clf.classify(features)
        hexad_profile = self.hexad.compute(batches)
        current_state = self._infer_current_state(batches[-1])

        return PlayerModel(
            player_id=player_id,
            session_id=session_id,
            timestamp=time.time(),
            current_state=current_state,
            flow_state=flow_state,
            flow_score=flow_score,
            challenge_skill_ratio=features["challenge_skill_ratio"],
            hexad_profile=hexad_profile,
            session_elapsed=batches[-1].session_elapsed,
        )

    def _infer_current_state(self, batch) -> CurrentState:
        if batch.kills > 0 or batch.damage_taken > 10:
            return CurrentState.IN_COMBAT
        if batch.npc_interactions_voluntary > 0 or batch.dialogue_lines_shown > 0:
            return CurrentState.IN_DIALOGUE
        if batch.tiles_explored > 0:
            return CurrentState.EXPLORING
        return CurrentState.IDLE

    def _default_model(self, player_id, session_id) -> PlayerModel:
        from backend.models.player_model import HexadProfile, FlowState
        return PlayerModel(
            player_id=player_id, session_id=session_id,
            timestamp=time.time(),
            current_state=CurrentState.IDLE,
            flow_state=FlowState.FLOW,
            flow_score=0.5,
            challenge_skill_ratio=1.0,
            hexad_profile=HexadProfile(),
        )
```

**Step 4: Run to verify passes**
```bash
pytest tests/test_api.py -v
```

**Step 5: Commit**
```bash
git add backend/player_modeling/modeling_service.py backend/routers/player_model.py
git commit -m "feat: player modeling service and REST endpoint"
```

---

## Task 7: ChromaDB Lore RAG Pipeline

**Files:**
- Create: `backend/narrative/rag_retriever.py`
- Create: `lore/world.md`, `lore/characters.md`, `lore/quests.md`
- Test: `backend/tests/test_narrative.py`

**Step 1: Write failing tests**
```python
# backend/tests/test_narrative.py
from backend.narrative.rag_retriever import LoreRetriever

def test_retriever_returns_relevant_lore():
    retriever = LoreRetriever(persist_dir=":memory:")
    retriever.add_document("The dungeon holds an ancient curse.", metadata={"source": "world"})
    retriever.add_document("Captain Aldric is a loyal but haunted soldier.", metadata={"source": "characters"})
    results = retriever.retrieve("tell me about the dungeon", top_k=1)
    assert len(results) == 1
    assert "dungeon" in results[0]["text"].lower()

def test_retriever_returns_empty_on_no_match():
    retriever = LoreRetriever(persist_dir=":memory:")
    retriever.add_document("The ocean is vast and blue.", metadata={"source": "world"})
    results = retriever.retrieve("spaceship laser cannon", top_k=3)
    # Should return something (semantic search) but no hard assertion — just valid list
    assert isinstance(results, list)
```

**Step 2: Run to verify fails**
```bash
pytest tests/test_narrative.py -v
```

**Step 3: Implement**
```python
# backend/narrative/rag_retriever.py
"""
ChromaDB-backed RAG retriever for game lore.
Uses sentence-transformers (all-MiniLM-L6-v2) for fast, local embeddings.
No internet required — fully offline.
"""
import chromadb
from chromadb.utils import embedding_functions
import uuid

class LoreRetriever:
    def __init__(self, persist_dir: str = "./data/chroma"):
        if persist_dir == ":memory:":
            self.client = chromadb.EphemeralClient()
        else:
            self.client = chromadb.PersistentClient(path=persist_dir)

        self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"   # 22MB, 384-dim, ~14ms/query
        )
        self.collection = self.client.get_or_create_collection(
            name="game_lore",
            embedding_function=self.ef,
            metadata={"hnsw:space": "cosine"}
        )

    def add_document(self, text: str, metadata: dict = None):
        self.collection.add(
            documents=[text],
            metadatas=[metadata or {}],
            ids=[str(uuid.uuid4())]
        )

    def add_documents_from_file(self, filepath: str, source: str):
        """Chunk markdown file into paragraphs and index."""
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        chunks = [p.strip() for p in content.split("\n\n") if p.strip()]
        for chunk in chunks:
            self.add_document(chunk, metadata={"source": source})

    def retrieve(self, query: str, top_k: int = 3) -> list[dict]:
        if self.collection.count() == 0:
            return []
        results = self.collection.query(
            query_texts=[query],
            n_results=min(top_k, self.collection.count()),
            include=["documents", "metadatas", "distances"]
        )
        return [
            {"text": doc, "source": meta.get("source",""), "distance": dist}
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            )
        ]
```

**Step 4: Create lore files**
```markdown
<!-- lore/world.md -->
# World Lore

The kingdom of Eryndal has fallen into shadow after the Sundering War.
Ancient seals that once contained the Void-touched creatures have crumbled.

The Thornwood Dungeon was once a royal armory but is now overrun by creatures
drawn to the broken seal at its deepest level.

The village of Ashfen sits at the dungeon's entrance, its population
dwindled to a handful of survivors who refuse to abandon their ancestral home.
```

```markdown
<!-- lore/characters.md -->
# Characters

**Captain Aldric** — A veteran soldier who failed to stop the Sundering.
He is haunted by guilt and seeks redemption through protecting Ashfen.
Voice: formal, melancholic, determined.

**Mira the Merchant** — A practical woman who trades in necessities.
She knows the dungeon better than she admits. Voice: dry, witty, cautious.

**The Stranger** — A mysterious figure at the edge of town.
Their motives are unknown. Voice: cryptic, detached, unsettling.
```

**Step 5: Run to verify passes**
```bash
pytest tests/test_narrative.py -v
```

**Step 6: Commit**
```bash
git add backend/narrative/rag_retriever.py lore/
git commit -m "feat: ChromaDB RAG lore retriever with sentence-transformers"
```

---

## Task 8: Episodic Session Memory

**Files:**
- Create: `backend/narrative/memory.py`
- Test: `backend/tests/test_narrative.py` (extend)

**Step 1: Write failing tests**
```python
# backend/tests/test_narrative.py (add)
from backend.narrative.memory import EpisodicMemory

def test_memory_stores_and_retrieves_events():
    mem = EpisodicMemory(max_events=5)
    mem.add_event("Player helped the merchant escape the dungeon.", importance=0.9)
    mem.add_event("Player ignored the guard captain's warning.", importance=0.7)
    summary = mem.get_context_summary()
    assert "merchant" in summary.lower()
    assert len(mem.events) == 2

def test_memory_respects_max_limit():
    mem = EpisodicMemory(max_events=3)
    for i in range(5):
        mem.add_event(f"Event {i}", importance=float(i)/5)
    assert len(mem.events) == 3  # Only top-3 by importance kept

def test_memory_returns_empty_summary_when_empty():
    mem = EpisodicMemory()
    assert mem.get_context_summary() == ""
```

**Step 2: Run to verify fails**
```bash
pytest tests/test_narrative.py -v
```

**Step 3: Implement**
```python
# backend/narrative/memory.py
"""
Lightweight episodic session memory for narrative consistency.
Inspired by EM-LLM (ICLR 2025) but simplified for real-time game use.
Stores key narrative events; injects them into LLM prompts.
"""
from dataclasses import dataclass, field
import heapq

@dataclass
class MemoryEvent:
    text: str
    importance: float       # 0.0-1.0 (designer or heuristic assigned)
    timestamp: float = 0.0

    def __lt__(self, other):
        return self.importance < other.importance

class EpisodicMemory:
    def __init__(self, max_events: int = 10):
        self.max_events = max_events
        self.events: list[MemoryEvent] = []

    def add_event(self, text: str, importance: float = 0.5, timestamp: float = 0.0):
        """Add a narrative event. Evicts lowest-importance when full."""
        event = MemoryEvent(text=text, importance=importance, timestamp=timestamp)
        self.events.append(event)
        if len(self.events) > self.max_events:
            # Keep top-N by importance
            self.events = heapq.nlargest(self.max_events, self.events, key=lambda e: e.importance)

    def get_context_summary(self) -> str:
        """Returns a compact narrative context string for prompt injection."""
        if not self.events:
            return ""
        sorted_events = sorted(self.events, key=lambda e: e.importance, reverse=True)
        lines = [f"- {e.text}" for e in sorted_events[:5]]  # top 5 in prompt
        return "KEY NARRATIVE EVENTS THIS SESSION:\n" + "\n".join(lines)

    def clear(self):
        self.events.clear()
```

**Step 4: Run to verify passes**
```bash
pytest tests/test_narrative.py -v
```

**Step 5: Commit**
```bash
git add backend/narrative/memory.py
git commit -m "feat: episodic session memory for narrative consistency"
```

---

## Task 9: Narrative Generation with RAG-Grounded Prompts

**Files:**
- Create: `backend/narrative/prompt_builder.py`
- Create: `backend/narrative/ollama_client.py`
- Test: `backend/tests/test_narrative.py` (extend)

**Step 1: Write failing tests**
```python
# backend/tests/test_narrative.py (add)
from backend.narrative.prompt_builder import PromptBuilder
from backend.models.player_model import PlayerModel, FlowState, CurrentState, HexadProfile
from backend.models.narrative import NarrativeAction
import time

def _make_player_model():
    return PlayerModel(
        player_id="p1", session_id="s1",
        timestamp=time.time(),
        current_state=CurrentState.IN_DIALOGUE,
        flow_state=FlowState.ANXIETY,
        flow_score=0.8,
        challenge_skill_ratio=1.6,
        hexad_profile=HexadProfile(socializer=0.9, explorer=0.7),
        session_elapsed=600
    )

def test_prompt_builder_includes_flow_state():
    builder = PromptBuilder()
    model = _make_player_model()
    system, user = builder.build(
        player_model=model,
        action=NarrativeAction.PROVIDE_GUIDANCE,
        location="Thornwood Dungeon Entrance",
        quest_stage="Find the broken seal",
        lore_context=["The dungeon holds ancient curses."],
        memory_context="- Player just died to the first enemy."
    )
    assert "ANXIETY" in user
    assert "PROVIDE_GUIDANCE" in user
    assert "dungeon" in user.lower()
    assert "Player just died" in user

def test_prompt_builder_system_prompt_has_constraints():
    builder = PromptBuilder()
    model = _make_player_model()
    system, _ = builder.build(
        player_model=model,
        action=NarrativeAction.ADD_MYSTERY,
        location="Ashfen Village"
    )
    assert "JSON" in system
    assert "fallback" in system
```

**Step 2: Run to verify fails**
```bash
pytest tests/test_narrative.py::test_prompt_builder_includes_flow_state -v
```

**Step 3: Implement**
```python
# backend/narrative/prompt_builder.py
from backend.models.player_model import PlayerModel
from backend.models.narrative import NarrativeAction

SYSTEM_TEMPLATE = """\
You are a narrative writer for a dark fantasy RPG.
Generate SHORT narrative content: dialogue (2-4 sentences) or descriptions (1-2 sentences).

STRICT RULES:
- Stay within the game world. No real-world references.
- Tone must match: {tone}
- Output ONLY valid JSON. No markdown, no explanation.
- If you cannot generate coherent content, output: {{"fallback": true}}

Output schema:
{{"type": "dialogue|description|quest_update",
  "content": "...",
  "speaker": "NPC name or null",
  "emotional_tone": "hopeful|neutral|tense|mysterious|humorous"}}
"""

USER_TEMPLATE = """\
PLAYER STATE:
- Flow State: {flow_state} (challenge/skill ratio: {ratio:.2f})
- Current Activity: {current_state}
- Session Time: {elapsed}s
- Playstyle: Explorer={explorer:.0%}, Socializer={socializer:.0%}, Achiever={achiever:.0%}, Disruptor={disruptor:.0%}

NARRATIVE ACTION: {action}
(LOWER_STAKES=ease tension, RAISE_STAKES=urgency, ADD_MYSTERY=curiosity hook,
 ADD_HUMOR=relief, PROVIDE_GUIDANCE=help struggling player,
 INCREASE_URGENCY=re-engage bored player, LORE_REWARD=discovery payoff)

CURRENT CONTEXT:
- Location: {location}
- Active Quest: {quest_stage}

RELEVANT LORE:
{lore_context}

{memory_context}

DESIGNER CONSTRAINTS:
- Forbidden topics: player's real world, fourth-wall breaks, anachronisms
- Keep consistent with above lore
- Character voices: Captain Aldric=formal/melancholic, Mira=dry/witty, Stranger=cryptic

Generate the narrative JSON now:
"""

TONE_MAP = {
    "ANXIETY": "urgent, supportive — player is struggling",
    "BOREDOM": "exciting, surprising — player needs stimulation",
    "FLOW": "immersive, atmospheric — maintain the experience",
    "APATHY": "intriguing, mysterious — re-engage the player",
}

class PromptBuilder:
    def build(
        self,
        player_model: PlayerModel,
        action: NarrativeAction,
        location: str = "Unknown",
        quest_stage: str = "None",
        lore_context: list[str] = None,
        memory_context: str = "",
    ) -> tuple[str, str]:
        tone = TONE_MAP.get(player_model.flow_state.value, "neutral")
        lore_str = "\n".join(f"- {l}" for l in (lore_context or []))
        if not lore_str:
            lore_str = "- No specific lore retrieved."

        system = SYSTEM_TEMPLATE.format(tone=tone)
        user = USER_TEMPLATE.format(
            flow_state=player_model.flow_state.value,
            ratio=player_model.challenge_skill_ratio,
            current_state=player_model.current_state.value,
            elapsed=int(player_model.session_elapsed),
            explorer=player_model.hexad_profile.explorer,
            socializer=player_model.hexad_profile.socializer,
            achiever=player_model.hexad_profile.achiever,
            disruptor=player_model.hexad_profile.disruptor,
            action=action.value,
            location=location,
            quest_stage=quest_stage,
            lore_context=lore_str,
            memory_context=memory_context,
        )
        return system, user
```

```python
# backend/narrative/ollama_client.py
"""
Ollama API client with JSON output validation and fallback handling.
Model: phi3.5 (3.8B, best reasoning/size tradeoff) or llama3.2:3b
"""
import httpx
import json
from backend.config import settings
from backend.models.narrative import NarrativeContent, NarrativeAction, NarrativeContentType

class OllamaClient:
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model

    async def generate(
        self, system_prompt: str, user_prompt: str, action: NarrativeAction
    ) -> NarrativeContent:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "format": "json",          # Ollama JSON mode — forces valid JSON output
            "options": {
                "temperature": 0.75,   # Balanced creativity/consistency
                "top_p": 0.9,
                "num_predict": 200,    # Max tokens — keeps responses short
            }
        }
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                )
                resp.raise_for_status()
                raw = resp.json()["message"]["content"]
                data = json.loads(raw)

                if data.get("fallback"):
                    return self._fallback_content(action)

                return NarrativeContent(
                    action_taken=action,
                    content_type=NarrativeContentType(data.get("type", "dialogue")),
                    content=data.get("content", ""),
                    speaker=data.get("speaker"),
                    emotional_tone=data.get("emotional_tone", "neutral"),
                )
        except Exception:
            return self._fallback_content(action)

    def _fallback_content(self, action: NarrativeAction) -> NarrativeContent:
        FALLBACKS = {
            NarrativeAction.PROVIDE_GUIDANCE: "The path ahead is treacherous. Tread carefully.",
            NarrativeAction.RAISE_STAKES: "Something stirs in the darkness. You feel watched.",
            NarrativeAction.ADD_MYSTERY: "A symbol on the wall catches your eye. You've seen it before.",
            NarrativeAction.LOWER_STAKES: "The air grows lighter here. A moment's respite.",
            NarrativeAction.INCREASE_URGENCY: "A distant sound echoes — something is coming.",
            NarrativeAction.ADD_HUMOR: "You trip slightly. A rat watches you, unimpressed.",
            NarrativeAction.LORE_REWARD: "You notice worn carvings that tell an old story.",
            NarrativeAction.NO_CHANGE: "",
        }
        return NarrativeContent(
            action_taken=action,
            content_type=NarrativeContentType.DESCRIPTION,
            content=FALLBACKS.get(action, ""),
            fallback=True
        )
```

**Step 4: Run to verify passes**
```bash
pytest tests/test_narrative.py -v
```

**Step 5: Commit**
```bash
git add backend/narrative/
git commit -m "feat: RAG-grounded prompt builder and Ollama client with fallbacks"
```

---

## Task 10: RL Environment (Gym MDP)

**Files:**
- Create: `backend/adaptation/rl_env.py`
- Create: `backend/adaptation/reward.py`
- Test: `backend/tests/test_rl_env.py`

**Step 1: Write failing tests**
```python
# backend/tests/test_rl_env.py
import numpy as np
import gymnasium as gym
from backend.adaptation.rl_env import NarrativeAdaptationEnv
from backend.adaptation.reward import compute_reward
from backend.models.player_model import FlowState

def test_env_has_valid_spaces():
    env = NarrativeAdaptationEnv()
    assert isinstance(env.observation_space, gym.spaces.Box)
    assert isinstance(env.action_space, gym.spaces.Discrete)
    assert env.action_space.n == 8  # 7 actions + NO_CHANGE

def test_env_reset_returns_valid_obs():
    env = NarrativeAdaptationEnv()
    obs, info = env.reset()
    assert obs.shape == env.observation_space.shape
    assert env.observation_space.contains(obs)

def test_env_step_returns_valid_tuple():
    env = NarrativeAdaptationEnv()
    env.reset()
    obs, reward, terminated, truncated, info = env.step(0)
    assert isinstance(reward, float)
    assert isinstance(terminated, bool)
    assert env.observation_space.contains(obs)

def test_reward_flow_is_positive():
    r = compute_reward(FlowState.FLOW, FlowState.FLOW, action=6, steps_in_state=5)
    assert r > 0

def test_reward_anxiety_is_negative():
    r = compute_reward(FlowState.FLOW, FlowState.ANXIETY, action=1, steps_in_state=1)
    assert r < 0

def test_reward_flow_streak_bonus():
    r_no_streak = compute_reward(FlowState.FLOW, FlowState.FLOW, action=6, steps_in_state=1)
    r_streak    = compute_reward(FlowState.FLOW, FlowState.FLOW, action=6, steps_in_state=5)
    assert r_streak > r_no_streak
```

**Step 2: Run to verify fails**
```bash
pytest tests/test_rl_env.py -v
```

**Step 3: Implement**
```python
# backend/adaptation/reward.py
from backend.models.player_model import FlowState

FLOW_REWARDS = {
    FlowState.FLOW:    +1.0,
    FlowState.BOREDOM: -0.3,
    FlowState.ANXIETY: -0.5,
    FlowState.APATHY:  -0.8,
}
STEP_PENALTY = -0.05        # encourages efficiency
REPETITION_PENALTY = -0.15  # discourages same action > 3 steps

def compute_reward(
    prev_state: FlowState,
    new_state: FlowState,
    action: int,
    steps_in_state: int,
    last_3_actions: list[int] = None,
) -> float:
    r = FLOW_REWARDS[new_state]
    r += STEP_PENALTY

    # Streak bonus: +0.2 for each consecutive FLOW step beyond 2
    if new_state == FlowState.FLOW and steps_in_state > 2:
        r += 0.2

    # Transition bonus: pulling player from bad state to flow
    if prev_state in (FlowState.ANXIETY, FlowState.BOREDOM) and new_state == FlowState.FLOW:
        r += 0.3

    # Repetition penalty
    if last_3_actions and len(set(last_3_actions)) == 1 and action in last_3_actions:
        r += REPETITION_PENALTY

    return float(r)
```

```python
# backend/adaptation/rl_env.py
"""
Gymnasium environment for narrative adaptation MDP.
State: 7-dim continuous vector derived from PlayerModel.
Action: discrete over 8 NarrativeActions.
Reward: see reward.py
"""
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from backend.models.player_model import FlowState
from backend.models.narrative import NarrativeAction
from backend.adaptation.reward import compute_reward

ACTIONS = list(NarrativeAction)

class NarrativeAdaptationEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, max_steps: int = 360):  # 30min / 5s window
        super().__init__()
        self.max_steps = max_steps

        # Observation: [flow_score, cs_ratio_norm, explorer, socializer,
        #               achiever, disruptor, session_progress]
        self.observation_space = spaces.Box(
            low=0.0, high=1.0, shape=(7,), dtype=np.float32
        )
        self.action_space = spaces.Discrete(len(ACTIONS))

        self._flow_state = FlowState.FLOW
        self._step_count = 0
        self._steps_in_state = 0
        self._last_3_actions: list[int] = []

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self._flow_state = FlowState.FLOW
        self._step_count = 0
        self._steps_in_state = 0
        self._last_3_actions = []
        return self._obs(), {}

    def step(self, action: int):
        prev_state = self._flow_state
        # Simulated transition (for training): action effect on flow state
        self._flow_state = self._simulate_transition(action, prev_state)

        if self._flow_state == prev_state:
            self._steps_in_state += 1
        else:
            self._steps_in_state = 1

        self._last_3_actions = (self._last_3_actions + [action])[-3:]
        reward = compute_reward(
            prev_state, self._flow_state, action,
            self._steps_in_state, self._last_3_actions
        )
        self._step_count += 1
        terminated = False
        truncated = self._step_count >= self.max_steps
        return self._obs(), reward, terminated, truncated, {"flow_state": self._flow_state.value}

    def _obs(self) -> np.ndarray:
        flow_score_map = {FlowState.FLOW:1.0, FlowState.BOREDOM:0.3,
                          FlowState.ANXIETY:0.2, FlowState.APATHY:0.1}
        return np.array([
            flow_score_map[self._flow_state],
            0.5,   # cs_ratio placeholder (real env uses live PlayerModel)
            0.5, 0.5, 0.5, 0.5,  # hexad dims placeholder
            min(self._step_count / self.max_steps, 1.0)
        ], dtype=np.float32)

    def _simulate_transition(self, action: int, current: FlowState) -> FlowState:
        """Probabilistic transition model for offline training."""
        rng = self.np_random if self.np_random else np.random.default_rng()
        effective_actions = {
            FlowState.ANXIETY: [4, 0],   # PROVIDE_GUIDANCE, LOWER_STAKES helpful
            FlowState.BOREDOM: [5, 1, 2],# URGENCY, RAISE_STAKES, MYSTERY helpful
            FlowState.APATHY:  [2, 6],   # MYSTERY, LORE_REWARD helpful
            FlowState.FLOW:    [7],       # NO_CHANGE maintains flow
        }
        helpful = effective_actions.get(current, [])
        if action in helpful:
            return FlowState.FLOW if rng.random() < 0.75 else current
        elif current == FlowState.FLOW:
            return FlowState.BOREDOM if rng.random() < 0.1 else FlowState.FLOW
        return current
```

**Step 4: Run to verify passes**
```bash
pytest tests/test_rl_env.py -v
```

**Step 5: Commit**
```bash
git add backend/adaptation/
git commit -m "feat: Gymnasium MDP environment and reward function for narrative RL"
```

---

## Task 11: PPO Agent Training

**Files:**
- Create: `backend/adaptation/agent.py`
- Create: `notebooks/rl_training.ipynb`

**Step 1: Train and verify reward curve**
```python
# backend/adaptation/agent.py
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.callbacks import EvalCallback
from backend.adaptation.rl_env import NarrativeAdaptationEnv
from backend.models.player_model import FlowState, PlayerModel
from backend.models.narrative import NarrativeAction
import numpy as np
from pathlib import Path

ACTIONS = list(NarrativeAction)
MODEL_PATH = "./data/ppo_narrative_agent"
HEURISTIC_MAP = {
    FlowState.ANXIETY:  4,   # PROVIDE_GUIDANCE
    FlowState.BOREDOM:  5,   # INCREASE_URGENCY
    FlowState.APATHY:   2,   # ADD_MYSTERY
    FlowState.FLOW:     7,   # NO_CHANGE
}

class NarrativeAgent:
    def __init__(self):
        self.model = self._load_or_train()

    def _load_or_train(self) -> PPO:
        path = Path(MODEL_PATH + ".zip")
        if path.exists():
            return PPO.load(MODEL_PATH, env=NarrativeAdaptationEnv())
        return self._train()

    def _train(self) -> PPO:
        env = make_vec_env(NarrativeAdaptationEnv, n_envs=4)
        model = PPO(
            "MlpPolicy", env,
            learning_rate=3e-4,
            n_steps=512, batch_size=64, n_epochs=10,
            gamma=0.95, gae_lambda=0.95, clip_range=0.2,
            verbose=1, tensorboard_log="./data/tb_logs/"
        )
        eval_env = NarrativeAdaptationEnv()
        eval_cb = EvalCallback(eval_env, best_model_save_path="./data/",
                               n_eval_episodes=10, eval_freq=5000)
        model.learn(total_timesteps=200_000, callback=eval_cb)
        model.save(MODEL_PATH)
        return model

    def select_action(self, player_model: PlayerModel) -> NarrativeAction:
        """Cold-start: heuristic for first 2 min, PPO thereafter."""
        if player_model.session_elapsed < 120:
            idx = HEURISTIC_MAP[player_model.flow_state]
            return ACTIONS[idx]

        obs = self._player_model_to_obs(player_model)
        action_idx, _ = self.model.predict(obs, deterministic=False)
        return ACTIONS[int(action_idx)]

    def _player_model_to_obs(self, pm: PlayerModel) -> np.ndarray:
        flow_score_map = {FlowState.FLOW:1.0, FlowState.BOREDOM:0.3,
                          FlowState.ANXIETY:0.2, FlowState.APATHY:0.1}
        return np.array([
            pm.flow_score,
            min(pm.challenge_skill_ratio / 3.0, 1.0),
            pm.hexad_profile.explorer,
            pm.hexad_profile.socializer,
            pm.hexad_profile.achiever,
            pm.hexad_profile.disruptor,
            min(pm.session_elapsed / 1800.0, 1.0)   # normalize to 30min session
        ], dtype=np.float32)
```

**Step 2: Train (run once)**
```bash
cd backend && python -c "from adaptation.agent import NarrativeAgent; NarrativeAgent()"
# Watch TensorBoard: tensorboard --logdir data/tb_logs/
# Expected: reward curve rises, FLOW% increases over training
```

**Step 3: Commit**
```bash
git add backend/adaptation/agent.py notebooks/
git commit -m "feat: PPO narrative adaptation agent with cold-start heuristic"
```

---

## Task 12: Narrative Generation REST Endpoint

**Files:**
- Create: `backend/routers/narrative.py`
- Test: `backend/tests/test_api.py` (extend)

**Step 1: Write failing test**
```python
# backend/tests/test_api.py (add)
def test_narrative_endpoint_returns_content(monkeypatch):
    """Test narrative endpoint returns valid content structure."""
    from backend.narrative.ollama_client import OllamaClient
    from backend.models.narrative import NarrativeContent, NarrativeAction, NarrativeContentType

    # Monkeypatch Ollama to avoid real LLM call in tests
    async def mock_generate(self, sys, usr, action):
        return NarrativeContent(
            action_taken=action,
            content_type=NarrativeContentType.DIALOGUE,
            content="The dungeon holds many secrets.",
            speaker="Captain Aldric",
            emotional_tone="tense"
        )
    monkeypatch.setattr(OllamaClient, "generate", mock_generate)

    client = TestClient(app)
    response = client.post("/api/narrative/generate", json={
        "session_id": "s1",
        "player_id": "p1",
        "location": "Dungeon Entrance",
        "quest_stage": "Find the seal"
    })
    assert response.status_code == 200
    data = response.json()
    assert "content" in data
    assert "action_taken" in data
```

**Step 2-4: Implement and verify (follow same TDD pattern)**

**Step 5: Commit**
```bash
git add backend/routers/narrative.py
git commit -m "feat: narrative generation REST endpoint with RL action selection"
```

---

## Task 13: Unity Plugin — PlayerDataLogger

**Files:**
- Create: `unity-plugin/Runtime/PluginConfig.cs`
- Create: `unity-plugin/Runtime/PlayerDataLogger.cs`
- Test: `unity-plugin/Tests/EditMode/TelemetryBatchTests.cs`

**Step 1: PluginConfig ScriptableObject**
```csharp
// unity-plugin/Runtime/PluginConfig.cs
using UnityEngine;

[CreateAssetMenu(fileName = "PluginConfig", menuName = "NarrativePlugin/Config")]
public class PluginConfig : ScriptableObject
{
    [Header("Backend Connection")]
    public string backendWsUrl = "ws://localhost:8000/ws/telemetry";
    public string backendApiUrl = "http://localhost:8000/api";

    [Header("Telemetry Settings")]
    [Range(2f, 15f)]
    public float telemetryIntervalSeconds = 5f;

    [Header("Session")]
    public string playerId = "player_001";
}
```

**Step 2: PlayerDataLogger**
```csharp
// unity-plugin/Runtime/PlayerDataLogger.cs
using System;
using System.Collections;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

[System.Serializable]
public class TelemetryBatch
{
    public string player_id;
    public string session_id;
    public double window_start;
    public double window_end;
    public int kills, deaths;
    public float damage_taken, damage_dealt;
    public int abilities_used, abilities_hit;
    public int objectives_completed, objectives_attempted;
    public int tiles_explored;
    public int total_tiles = 100;
    public int npc_interactions_voluntary;
    public int dialogue_lines_shown, dialogue_lines_skipped;
    public int lore_items_read, lore_items_found;
    public float idle_seconds;
    public float session_elapsed;
    public string current_location = "unknown";
    public string current_objective = "none";
}

public class PlayerDataLogger : MonoBehaviour
{
    [SerializeField] private PluginConfig config;

    private TelemetryBatch _currentBatch;
    private string _sessionId;
    private float _windowStart;
    private float _sessionStart;

    // Call these from your game systems:
    public void OnKill()      => _currentBatch.kills++;
    public void OnDeath()     => _currentBatch.deaths++;
    public void OnDamageTaken(float amt) => _currentBatch.damage_taken += amt;
    public void OnDamageDealt(float amt) => _currentBatch.damage_dealt += amt;
    public void OnAbilityUsed(bool hit)  { _currentBatch.abilities_used++; if(hit) _currentBatch.abilities_hit++; }
    public void OnObjectiveAttempted()   => _currentBatch.objectives_attempted++;
    public void OnObjectiveCompleted()   => _currentBatch.objectives_completed++;
    public void OnTileExplored(int count) => _currentBatch.tiles_explored = count;
    public void OnVoluntaryNPCInteraction() => _currentBatch.npc_interactions_voluntary++;
    public void OnDialogueShown()  => _currentBatch.dialogue_lines_shown++;
    public void OnDialogueSkipped() => _currentBatch.dialogue_lines_skipped++;
    public void OnLoreItemFound()   => _currentBatch.lore_items_found++;
    public void OnLoreItemRead()    => _currentBatch.lore_items_read++;

    private void Awake()
    {
        _sessionId = Guid.NewGuid().ToString();
        _sessionStart = Time.time;
        StartNewBatch();
        InvokeRepeating(nameof(SendBatch), config.telemetryIntervalSeconds, config.telemetryIntervalSeconds);
    }

    private void StartNewBatch()
    {
        _windowStart = Time.time;
        _currentBatch = new TelemetryBatch {
            player_id = config.playerId,
            session_id = _sessionId,
            window_start = _windowStart,
        };
    }

    private void SendBatch()
    {
        _currentBatch.window_end = Time.time;
        _currentBatch.session_elapsed = Time.time - _sessionStart;
        var json = JsonUtility.ToJson(_currentBatch);
        StartCoroutine(PostTelemetry(json));
        StartNewBatch();
    }

    private IEnumerator PostTelemetry(string json)
    {
        var req = new UnityWebRequest(config.backendApiUrl + "/telemetry-http", "POST");
        req.uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes(json));
        req.downloadHandler = new DownloadHandlerBuffer();
        req.SetRequestHeader("Content-Type", "application/json");
        yield return req.SendWebRequest();
    }
}
```

**Step 3: Commit**
```bash
git add unity-plugin/
git commit -m "feat: Unity PlayerDataLogger with telemetry batch collection"
```

---

## Task 14: Unity Plugin — NarrativeManager & ContentInjector

**Files:**
- Create: `unity-plugin/Runtime/NarrativeManager.cs`
- Create: `unity-plugin/Runtime/ContentInjector.cs`

```csharp
// unity-plugin/Runtime/NarrativeManager.cs
using System.Collections;
using UnityEngine;
using UnityEngine.Networking;

[System.Serializable]
public class NarrativeRequest
{
    public string session_id;
    public string player_id;
    public string location;
    public string quest_stage;
}

[System.Serializable]
public class NarrativeResponse
{
    public string action_taken;
    public string content_type;
    public string content;
    public string speaker;
    public string emotional_tone;
    public bool fallback;
}

public class NarrativeManager : MonoBehaviour
{
    [SerializeField] private PluginConfig config;
    [SerializeField] private ContentInjector injector;
    [SerializeField] private PlayerDataLogger logger;

    [Header("Context (update from game systems)")]
    public string currentLocation = "Ashfen Village";
    public string currentQuestStage = "Find the broken seal";

    [Range(10f, 60f)]
    public float narrativePollingInterval = 30f;

    private void Start()
    {
        InvokeRepeating(nameof(RequestNarrative), 30f, narrativePollingInterval);
    }

    private void RequestNarrative()
    {
        StartCoroutine(FetchNarrative());
    }

    private IEnumerator FetchNarrative()
    {
        var req = new NarrativeRequest {
            session_id = GetComponent<PlayerDataLogger>() != null
                ? System.Guid.NewGuid().ToString() : "default",
            player_id = config.playerId,
            location = currentLocation,
            quest_stage = currentQuestStage
        };
        var json = JsonUtility.ToJson(req);
        var webReq = new UnityWebRequest(config.backendApiUrl + "/narrative/generate", "POST");
        webReq.uploadHandler = new UploadHandlerRaw(System.Text.Encoding.UTF8.GetBytes(json));
        webReq.downloadHandler = new DownloadHandlerBuffer();
        webReq.SetRequestHeader("Content-Type", "application/json");
        yield return webReq.SendWebRequest();

        if (webReq.result == UnityWebRequest.Result.Success)
        {
            var response = JsonUtility.FromJson<NarrativeResponse>(webReq.downloadHandler.text);
            injector.Apply(response);
        }
    }
}
```

```csharp
// unity-plugin/Runtime/ContentInjector.cs
using UnityEngine;
using UnityEngine.Events;

public class ContentInjector : MonoBehaviour
{
    [Header("Events — wire these to your game systems")]
    public UnityEvent<string, string> OnDialogueInjected;  // (speaker, text)
    public UnityEvent<string> OnDescriptionInjected;        // (text)
    public UnityEvent<string> OnQuestUpdateInjected;        // (text)

    public void Apply(NarrativeResponse response)
    {
        if (response.fallback || string.IsNullOrEmpty(response.content)) return;

        switch (response.content_type)
        {
            case "dialogue":
                OnDialogueInjected?.Invoke(response.speaker ?? "NPC", response.content);
                break;
            case "description":
                OnDescriptionInjected?.Invoke(response.content);
                break;
            case "quest_update":
                OnQuestUpdateInjected?.Invoke(response.content);
                break;
        }
    }
}
```

**Commit:**
```bash
git add unity-plugin/Runtime/
git commit -m "feat: NarrativeManager polling loop and ContentInjector event system"
```

---

## Task 15: Testbed Game (Unity 6)

**Files:**
- Create: `testbed-game/Assets/Scripts/GameManager.cs`
- Create: `testbed-game/Assets/Scripts/NPCDialogueController.cs`
- Create: `testbed-game/Assets/Scripts/TelemetryHooks.cs`

**Architecture:**
- 2D top-down view, Unity 6 default 2D Core template
- 3 scenes: Village Hub, Dungeon Room A (combat), Dungeon Room B (exploration)
- 3 NPCs with injectable dialogue queues
- Combat system with adjustable enemy HP/count
- Event-driven telemetry hooks (no polling, all event-driven)

**Control condition implementation:**
- Separate ScriptableObject: `StaticNarrativeContent.asset`
- Pre-authored for all 7 action types × 3 locations × 3 NPCs = 63 strings
- Loaded in control condition instead of calling backend
- 2 independent raters score parity (Cohen's κ target > 0.7)

**Commit:**
```bash
git add testbed-game/
git commit -m "feat: testbed game with telemetry hooks and NPC dialogue injection"
```

---

## Task 16: Evaluation Instruments & Analysis Scripts

**Files:**
- Create: `evaluation/questionnaires/geq_core.md`
- Create: `evaluation/questionnaires/minipxi.md`
- Create: `evaluation/questionnaires/personalization_scale.md`
- Create: `evaluation/questionnaires/interview_guide.md`
- Create: `evaluation/analysis/stats_analysis.py`

**GEQ Core (scoring reference):**
- Immersion subscale: items 3,12,18,19,27,30 — mean score
- Flow subscale: items 5,13,25,28,31 — mean score (PRIMARY DV)
- Positive Affect: items 1,4,8,20,29
- All items 0-4 Likert

**miniPXI (11 items, 7-point Likert):**
- Covers: Mastery, Curiosity, Immersion, Autonomy, Meaning + 5 functional
- Use validated 2022 version from dl.acm.org/doi/10.1145/3549507

**Custom Personalization Scale (3 items, 7-point):**
```
1. "The story felt tailored to how I was playing."
2. "The narrative responded to my choices and actions."
3. "The game seemed to understand what kind of player I am."
```

**Analysis script:**
```python
# evaluation/analysis/stats_analysis.py
import pandas as pd
from scipy import stats
import pingouin as pg

def run_t_tests(df: pd.DataFrame) -> dict:
    """
    df columns: condition (Experimental/Control), geq_flow, geq_immersion,
                geq_positive_affect, personalization, voluntary_npc,
                dialogue_read_ratio, exploration_coverage
    """
    results = {}
    dvs = ["geq_flow", "geq_immersion", "personalization",
           "voluntary_npc", "dialogue_read_ratio"]

    for dv in dvs:
        exp = df[df["condition"]=="Experimental"][dv].dropna()
        ctrl = df[df["condition"]=="Control"][dv].dropna()
        t, p = stats.ttest_ind(exp, ctrl)
        d = pg.compute_effsize(exp, ctrl, eftype="cohen")
        results[dv] = {"t": round(t,3), "p": round(p,4),
                       "cohen_d": round(d,3), "exp_mean": round(exp.mean(),3),
                       "ctrl_mean": round(ctrl.mean(),3)}
    return results
```

**Commit:**
```bash
git add evaluation/
git commit -m "feat: evaluation instruments, analysis scripts, interview guide"
```

---

## Testing Checklist (Before User Study)

```
□ Backend /health returns 200
□ WebSocket accepts telemetry and stores to SQLite
□ Player model endpoint returns valid JSON with all fields
□ Flow classifier correctly returns ANXIETY on hard-play data
□ Flow classifier correctly returns BOREDOM on easy-play data
□ Hexad explorer dimension > 0.6 on exploration-heavy play
□ RAG retriever returns lore relevant to query
□ Ollama generates valid JSON content (test manually with each action type)
□ Ollama fallback fires correctly on model error
□ PPO reward curve shows increasing FLOW% over 200k timesteps
□ PPO selects heuristic action for first 120s of session
□ Unity telemetry fires on kill, death, tile explored (test with mock scene)
□ Content injection triggers UnityEvent on dialogue content
□ Latency: full pipeline (telemetry → narrative) < 3 seconds on local hardware
□ Control condition static content passes inter-rater reliability (κ > 0.7)
□ Questionnaires pilot-tested on 3 internal participants
```

---

## Novelty Claims Summary

| Contribution | What's New | Comparison |
|---|---|---|
| Hexad-derived Continuous Profile | 6-dim real-valued vector vs. binary Bartle types | PANGeA uses Big Five (personality, not playstyle) |
| RAG-Grounded Narrative | ChromaDB lore + dynamic prompt | PANGeA/LIGS use static prompts only |
| Episodic Session Memory | In-session event memory injected into prompt | No comparable game system |
| PPO Narrative Adaptation | RL applied to narrative action selection | DDA systems target mechanical difficulty only |
| Flow-Based MDP Reward | Challenge-skill ratio as observable, Flow as reward | Prior RL-DDA uses completion time/score only |
| Closed-Loop Architecture | All 5 modules integrated | Prior work: siloed components |

---

## References (Key Papers to Cite)

- PANGeA (AAAI AIIDE 2024) — closest comparable system
- LIGS (CHI 2025) — LLM emergent narrative
- player2vec (arXiv, April 2024) — Transformer player embedding
- EM-LLM (ICLR 2025) — episodic memory for LLMs
- Hexad (Tondello et al., 2016) — player typology
- Csikszentmihalyi (1990) — Flow theory
- SB3 + PPO (Raffin et al., 2021) — RL framework
- ChromaDB / sentence-transformers (2024 docs)
- GEQ (IJsselsteijn et al., TU/e) — evaluation
- miniPXI (ACM CSCW 2022) — evaluation
- Braun & Clarke (2006, updated 2019/2022) — Thematic Analysis
- "Closing the Loop" systematic review (arXiv, May 2025) — gap statement
