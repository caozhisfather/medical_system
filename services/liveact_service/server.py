from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .liveact_adapter import LiveActAdapter
from .schemas import LiveActResponse, LiveActSpeakRequest, LiveActStatusRequest

app = FastAPI(title="真实数字人适配服务", version="0.1.0")
adapter = LiveActAdapter()
session_states: dict[str, dict[str, str]] = {}
app.mount("/generated-videos", StaticFiles(directory=adapter.config.video_save_path), name="generated-videos")


@app.get("/health")
def health() -> dict[str, object]:
    return adapter.health()


@app.get("/kernel-health")
def kernel_health() -> dict[str, object]:
    return adapter.kernel_runtime.status()


@app.post("/speak", response_model=LiveActResponse)
def speak(payload: LiveActSpeakRequest) -> LiveActResponse:
    result = adapter.speak(payload)
    session_states[payload.session_id] = {"state": result.state, "detail": result.subtitle}
    return result


@app.post("/status")
def status(payload: LiveActStatusRequest) -> dict[str, str]:
    session_states[payload.session_id] = {"state": payload.state, "detail": payload.detail}
    return {"status": "ok", "session_id": payload.session_id, "state": payload.state}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("services.liveact_service.server:app", host="127.0.0.1", port=8090, reload=True)
