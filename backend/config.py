from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "phi3.5"
    chroma_persist_dir: str = "./data/chroma"
    sqlite_path: str = "./data/telemetry.db"
    telemetry_window_seconds: int = 5
    flow_cold_start_seconds: int = 120

settings = Settings()
