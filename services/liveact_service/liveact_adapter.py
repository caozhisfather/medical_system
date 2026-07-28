from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path

from .kernel_runtime import KernelRuntimeProbe
from .mock_liveact import mock_response, state_from_request
from .schemas import LiveActResponse, LiveActSpeakRequest

SERVICE_DIR = Path(__file__).resolve().parent


def env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name, str(default)).strip().lower()
    return value in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class LiveActConfig:
    execution_mode: str = os.getenv("LIVEACT_EXECUTION_MODE", "mock")
    repo_path: Path = Path(os.getenv("LIVEACT_REPO_PATH", ""))
    ckpt_dir: Path = Path(os.getenv("LIVEACT_CKPT_DIR", ""))
    wav2vec_dir: Path = Path(os.getenv("LIVEACT_WAV2VEC_DIR", ""))
    video_save_path: Path = Path(os.getenv("LIVEACT_VIDEO_SAVE_PATH", str(SERVICE_DIR / "generated_videos")))
    size: str = os.getenv("LIVEACT_SIZE", "416*720")
    fps: int = int(os.getenv("LIVEACT_FPS", "24"))
    device: str = os.getenv("LIVEACT_DEVICE", "cuda:0")
    enable_fp8_kv_cache: bool = env_flag("LIVEACT_ENABLE_FP8_KV_CACHE")
    enable_block_offload: bool = env_flag("LIVEACT_ENABLE_BLOCK_OFFLOAD")
    enable_t5_cpu: bool = env_flag("LIVEACT_ENABLE_T5_CPU", True)
    command_timeout_seconds: int = int(os.getenv("LIVEACT_COMMAND_TIMEOUT_SECONDS", "900"))


class LiveActAdapter:
    """Prepares SoulX-LiveAct input and invokes it only when explicitly enabled."""

    def __init__(self, config: LiveActConfig | None = None) -> None:
        self.config = config or LiveActConfig()
        self.kernel_runtime = KernelRuntimeProbe()
        self.config.video_save_path.mkdir(parents=True, exist_ok=True)

    def health(self) -> dict[str, object]:
        return {
            "status": "ok",
            "execution_mode": self.config.execution_mode,
            "ready_for_liveact": self.ready_for_liveact(),
            "repo_path": str(self.config.repo_path),
            "checkpoint_configured": self.config.ckpt_dir.exists(),
            "wav2vec_configured": self.config.wav2vec_dir.exists(),
            "kernel_acceleration": self.kernel_runtime.status(),
        }

    def speak(self, payload: LiveActSpeakRequest) -> LiveActResponse:
        if payload.mode != "liveact" or self.config.execution_mode != "command":
            return mock_response(payload)
        if not self.ready_for_liveact():
            return mock_response(payload, "SoulX-LiveAct repo, checkpoints or wav2vec directory is not configured.")

        try:
            input_path = self.build_input_json(payload)
            completed = subprocess.run(
                self.build_command(input_path),
                cwd=self.config.repo_path,
                check=True,
                capture_output=True,
                text=True,
                timeout=self.config.command_timeout_seconds,
                shell=False,
                env=self._command_env(),
            )
            video_path = self._latest_video()
            if video_path is None:
                return mock_response(payload, f"Inference completed without a video file. {completed.stderr[-300:]}")
            return LiveActResponse(
                status="ok",
                session_id=payload.session_id,
                request_id=f"liveact-{uuid.uuid4().hex[:10]}",
                mode="liveact",
                state=state_from_request(payload),
                video_url=f"/generated-videos/{video_path.name}",
                subtitle=payload.text,
                emotion=payload.emotion,
                action=payload.action,
                duration=round(max(2.5, len(payload.text) / 5.2), 1),
                provider=f"SoulX-LiveAct + {self.kernel_runtime.status()['selected_backend']}",
            )
        except (OSError, subprocess.SubprocessError, TimeoutError, ValueError) as exc:
            return mock_response(payload, f"{type(exc).__name__}: {exc}")

    def build_input_json(self, payload: LiveActSpeakRequest) -> Path:
        """Create an adapter-owned input file; map fields after cloning the official repo."""
        request_id = uuid.uuid4().hex[:12]
        input_dir = self.config.video_save_path / "inputs"
        input_dir.mkdir(parents=True, exist_ok=True)
        input_path = input_dir / f"{payload.session_id}-{request_id}.json"
        audio_path = payload.audio_url or os.getenv("LIVEACT_MOCK_TTS_AUDIO", "")
        input_payload = {
            "session_id": payload.session_id,
            "avatar_id": payload.avatar_id,
            "text": payload.text,
            "audio_path": audio_path,
            "emotion": payload.emotion,
            "action": payload.action,
            "voice": payload.voice,
            "adapter_note": "Translate these stable app fields to the checked-out SoulX-LiveAct example schema.",
        }
        input_path.write_text(json.dumps(input_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return input_path

    def build_command(self, input_path: Path) -> list[str]:
        command = [
            sys.executable,
            str(self.config.repo_path / "generate.py"),
            "--size",
            self.config.size,
            "--ckpt_dir",
            str(self.config.ckpt_dir),
            "--wav2vec_dir",
            str(self.config.wav2vec_dir),
            "--fps",
            str(self.config.fps),
            "--input_json",
            str(input_path),
        ]
        if self.config.enable_fp8_kv_cache:
            command.append("--fp8_kv_cache")
        if self.config.enable_block_offload:
            command.append("--block_offload")
        if self.config.enable_t5_cpu:
            command.append("--t5_cpu")
        return command

    def ready_for_liveact(self) -> bool:
        return (
            self.config.execution_mode == "command"
            and (self.config.repo_path / "generate.py").exists()
            and self.config.ckpt_dir.exists()
            and self.config.wav2vec_dir.exists()
        )

    def _latest_video(self) -> Path | None:
        videos = sorted(
            list(self.config.video_save_path.glob("*.mp4")) + list(self.config.video_save_path.glob("*.webm")),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        return videos[0] if videos else None

    def _command_env(self) -> dict[str, str]:
        env = os.environ.copy()
        device_index = self.config.device.split(":")[-1] if ":" in self.config.device else self.config.device
        env.setdefault("CUDA_VISIBLE_DEVICES", device_index)
        env.setdefault("USE_CHANNELS_LAST_3D", "1")
        env.update(self.kernel_runtime.command_environment())
        return env
