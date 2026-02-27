import sqlite3
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
                window_start REAL NOT NULL,
                window_end REAL NOT NULL,
                data TEXT NOT NULL
            )
        """)
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_session ON telemetry(session_id)"
        )
        self.conn.commit()

    def insert(self, batch: TelemetryBatch) -> None:
        self.conn.execute(
            "INSERT INTO telemetry "
            "(player_id, session_id, window_start, window_end, data) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                batch.player_id,
                batch.session_id,
                batch.window_start,
                batch.window_end,
                batch.model_dump_json(),
            ),
        )
        self.conn.commit()

    def get_session(self, session_id: str) -> list[TelemetryBatch]:
        rows = self.conn.execute(
            "SELECT data FROM telemetry "
            "WHERE session_id = ? "
            "ORDER BY window_start ASC",
            (session_id,),
        ).fetchall()
        return [TelemetryBatch.model_validate_json(r[0]) for r in rows]

    def get_last_n(self, session_id: str, n: int = 10) -> list[TelemetryBatch]:
        rows = self.conn.execute(
            "SELECT data FROM telemetry "
            "WHERE session_id = ? "
            "ORDER BY window_start DESC "
            "LIMIT ?",
            (session_id, n),
        ).fetchall()
        # DESC gives newest first; reverse so caller gets ascending time order
        return [TelemetryBatch.model_validate_json(r[0]) for r in rows][::-1]
