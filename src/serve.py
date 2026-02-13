from fastapi import FastAPI
from fastapi.responses import JSONResponse
import datetime

app = FastAPI()

@app.get("/health")
async def health():
    """Simple health check returning status and current UTC time."""
    return JSONResponse({"status": "ok", "time": datetime.datetime.now(datetime.timezone.utc).isoformat()})

@app.get("/")
async def root():
    return JSONResponse({"message": "MindHarbor API running"})
