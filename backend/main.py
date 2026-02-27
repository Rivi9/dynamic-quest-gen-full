from fastapi import FastAPI

app = FastAPI(title="Narrative Personalization API", version="0.1.0")

@app.get("/health")
async def health():
    return {"status": "ok"}
