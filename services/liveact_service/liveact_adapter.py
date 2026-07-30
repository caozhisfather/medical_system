from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import threading
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
    execution_mode: str = os.getenv("LIVEACT_EXECUTION_MODE", "mock").strip().lower()
    repo_path: Path = Path(os.getenv("LIVEACT_REPO_PATH", ""))
    ckpt_dir: Path = Path(os.getenv("LIVEACT_CKPT_DIR", ""))
    wav2vec_dir: Path = Path(os.getenv("LIVEACT_WAV2VEC_DIR", ""))
    video_save_path: Path = Path(
        os.getenv("LIVEACT_VIDEO_SAVE_PATH", str(SERVICE_DIR / "generated_videos"))
    )
    size: str = os.getenv("LIVEACT_SIZE", "416*720")
    fps: int = int(os.getenv("LIVEACT_FPS", "25"))
    device: str = os.getenv("LIVEACT_DEVICE", "cuda:0")
    enable_fp8_kv_cache: bool = env_flag("LIVEACT_ENABLE_FP8_KV_CACHE")
    enable_block_offload: bool = env_flag("LIVEACT_ENABLE_BLOCK_OFFLOAD")
    enable_t5_cpu: bool = env_flag("LIVEACT_ENABLE_T5_CPU", True)
    command_timeout_seconds: int = int(os.getenv("LIVEACT_COMMAND_TIMEOUT_SECONDS", "300"))

    musetalk_repo_path: Path = Path(
        os.getenv("MUSETALK_REPO_PATH", "/home/zojer/ai-avatar/MuseTalk")
    )
    musetalk_python: Path = Path(
        os.getenv("MUSETALK_PYTHON", "/home/zojer/ai-avatar/env/bin/python")
    )
    musetalk_model_dir: Path = Path(
        os.getenv("MUSETALK_MODEL_DIR", "/home/zojer/ai-avatar/MuseTalk/models")
    )
    musetalk_runtime_dir: Path = Path(
        os.getenv("MUSETALK_RUNTIME_DIR", "/home/zojer/ai-avatar/runtime")
    )
    musetalk_avatar_image: Path = Path(
        os.getenv(
            "MUSETALK_AVATAR_IMAGE",
            "/mnt/d/cc项目/ai+medicine/图片/教学数字人.png",
        )
    )
    musetalk_avatar_video: Path = Path(
        os.getenv(
            "MUSETALK_AVATAR_VIDEO",
            "/home/zojer/ai-avatar/runtime/medical-tutor-idle.mp4",
        )
    )
    musetalk_tts_voice: str = os.getenv(
        "MUSETALK_TTS_VOICE", "zh-CN-XiaoxiaoNeural"
    )
    musetalk_max_text_length: int = int(os.getenv("MUSETALK_MAX_TEXT_LENGTH", "180"))
    musetalk_batch_size: int = int(os.getenv("MUSETALK_BATCH_SIZE", "1"))
    musetalk_use_float16: bool = env_flag("MUSETALK_USE_FLOAT16", True)


class LiveActAdapter:
    """Run a local talking-avatar backend while preserving the existing API."""

    def __init__(self, config: LiveActConfig | None = None) -> None:
        self.config = config or LiveActConfig()
        self.kernel_runtime = KernelRuntimeProbe()
        self._inference_lock = threading.Lock()
        self.config.video_save_path.mkdir(parents=True, exist_ok=True)
        self.config.musetalk_runtime_dir.mkdir(parents=True, exist_ok=True)

    def health(self) -> dict[str, object]:
        missing = self._musetalk_missing_files() if self.config.execution_mode == "musetalk" else []
        return {
            "status": "ok",
            "execution_mode": self.config.execution_mode,
            "provider": self._provider_name(),
            "ready_for_liveact": self.ready_for_liveact(),
            "repo_path": str(
                self.config.musetalk_repo_path
                if self.config.execution_mode == "musetalk"
                else self.config.repo_path
            ),
            "checkpoint_configured": not missing,
            "missing_files": missing,
            "avatar_configured": (
                self.config.musetalk_avatar_video.exists()
                or self.config.musetalk_avatar_image.exists()
            ),
            "kernel_acceleration": self.kernel_runtime.status(),
        }

    def speak(self, payload: LiveActSpeakRequest) -> LiveActResponse:
        if payload.mode != "liveact":
            return mock_response(payload)
        if not self.ready_for_liveact():
            return mock_response(
                payload,
                f"{self._provider_name()} is not ready: {', '.join(self._musetalk_missing_files()) or 'configuration missing'}.",
            )

        try:
            with self._inference_lock:
                if self.config.execution_mode == "musetalk":
                    return self._speak_musetalk(payload)
                return self._speak_soulx(payload)
        except (OSError, subprocess.SubprocessError, TimeoutError, ValueError) as exc:
            return mock_response(payload, f"{type(exc).__name__}: {exc}")

    def _speak_musetalk(self, payload: LiveActSpeakRequest) -> LiveActResponse:
        request_id = f"musetalk-{uuid.uuid4().hex[:10]}"
        safe_session = self._safe_name(payload.session_id)
        output_name = f"{safe_session}-{request_id}.mp4"
        audio_path, generated_audio = self._prepare_audio(payload, request_id)
        avatar_video = self._ensure_avatar_video()
        input_dir = self.config.musetalk_runtime_dir / "inputs"
        result_dir = self.config.musetalk_runtime_dir / "results"
        input_dir.mkdir(parents=True, exist_ok=True)
        result_dir.mkdir(parents=True, exist_ok=True)
        input_path = input_dir / f"{request_id}.json"
        input_path.write_text(
            json.dumps(
                {
                    request_id: {
                        "video_path": str(avatar_video),
                        "audio_path": str(audio_path),
                    }
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        command = [
            str(self.config.musetalk_python),
            "-m",
            "scripts.inference",
            "--inference_config",
            str(input_path),
            "--result_dir",
            str(result_dir),
            "--unet_model_path",
            str(self.config.musetalk_model_dir / "musetalkV15" / "unet.pth"),
            "--unet_config",
            str(self.config.musetalk_model_dir / "musetalkV15" / "musetalk.json"),
            "--whisper_dir",
            str(self.config.musetalk_model_dir / "whisper"),
            "--version",
            "v15",
            "--ffmpeg_path",
            str(self.config.musetalk_python.parent),
            "--fps",
            str(self.config.fps),
            "--batch_size",
            str(self.config.musetalk_batch_size),
            "--output_vid_name",
            output_name,
            "--saved_coord",
            "--use_saved_coord",
        ]
        if self.config.musetalk_use_float16:
            command.append("--use_float16")

        try:
            completed = subprocess.run(
                command,
                cwd=self.config.musetalk_repo_path,
                check=True,
                capture_output=True,
                text=True,
                timeout=self.config.command_timeout_seconds,
                shell=False,
                env=self._command_env(),
            )
            generated_video = result_dir / "v15" / output_name
            if not generated_video.exists():
                raise ValueError(
                    f"MuseTalk completed without video output. {completed.stderr[-400:]}"
                )
            destination = self.config.video_save_path / output_name
            shutil.copy2(generated_video, destination)
            duration = self._video_duration(destination, payload.text)
            return LiveActResponse(
                status="ok",
                session_id=payload.session_id,
                request_id=request_id,
                mode="liveact",
                state=state_from_request(payload),
                video_url=f"/generated-videos/{destination.name}",
                subtitle=payload.text,
                emotion=payload.emotion,
                action=payload.action,
                duration=duration,
                provider="MuseTalk 1.5（CUDA）+ Edge TTS",
            )
        finally:
            input_path.unlink(missing_ok=True)
            if generated_audio:
                audio_path.unlink(missing_ok=True)

    def _prepare_audio(
        self, payload: LiveActSpeakRequest, request_id: str
    ) -> tuple[Path, bool]:
        if payload.audio_url:
            candidate = Path(payload.audio_url.removeprefix("file://"))
            if not candidate.is_file():
                raise ValueError("Only an existing local audio file is accepted.")
            return candidate, False

        audio_dir = self.config.musetalk_runtime_dir / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        audio_path = audio_dir / f"{request_id}.mp3"
        edge_tts = self.config.musetalk_python.parent / "edge-tts"
        if not edge_tts.exists():
            raise ValueError(f"Edge TTS executable not found: {edge_tts}")
        text = payload.text[: self.config.musetalk_max_text_length]
        voice = (
            payload.voice
            if payload.voice.startswith(("zh-", "en-", "ja-", "ko-"))
            else self.config.musetalk_tts_voice
        )
        subprocess.run(
            [
                str(edge_tts),
                "--voice",
                voice,
                "--text",
                text,
                "--write-media",
                str(audio_path),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=90,
            shell=False,
        )
        if not audio_path.exists() or audio_path.stat().st_size < 1000:
            raise ValueError("TTS completed without usable audio.")
        return audio_path, True

    def _ensure_avatar_video(self) -> Path:
        if self.config.musetalk_avatar_video.exists():
            return self.config.musetalk_avatar_video
        if not self.config.musetalk_avatar_image.exists():
            raise ValueError(
                f"Avatar image not found: {self.config.musetalk_avatar_image}"
            )
        self.config.musetalk_avatar_video.parent.mkdir(parents=True, exist_ok=True)
        ffmpeg = self.config.musetalk_python.parent / "ffmpeg"
        subprocess.run(
            [
                str(ffmpeg),
                "-y",
                "-v",
                "error",
                "-loop",
                "1",
                "-i",
                str(self.config.musetalk_avatar_image),
                "-t",
                "1",
                "-r",
                str(self.config.fps),
                "-vf",
                "scale=1280:-2,format=yuv420p",
                "-c:v",
                "libx264",
                str(self.config.musetalk_avatar_video),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=90,
            shell=False,
        )
        return self.config.musetalk_avatar_video

    def _speak_soulx(self, payload: LiveActSpeakRequest) -> LiveActResponse:
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
            return mock_response(
                payload,
                f"SoulX-LiveAct completed without a video file. {completed.stderr[-300:]}",
            )
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

    def build_input_json(self, payload: LiveActSpeakRequest) -> Path:
        request_id = uuid.uuid4().hex[:12]
        input_dir = self.config.video_save_path / "inputs"
        input_dir.mkdir(parents=True, exist_ok=True)
        input_path = input_dir / f"{payload.session_id}-{request_id}.json"
        input_path.write_text(
            json.dumps(
                {
                    "session_id": payload.session_id,
                    "avatar_id": payload.avatar_id,
                    "text": payload.text,
                    "audio_path": payload.audio_url
                    or os.getenv("LIVEACT_MOCK_TTS_AUDIO", ""),
                    "emotion": payload.emotion,
                    "action": payload.action,
                    "voice": payload.voice,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
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
        if self.config.execution_mode == "musetalk":
            return not self._musetalk_missing_files() and (
                self.config.musetalk_avatar_video.exists()
                or self.config.musetalk_avatar_image.exists()
            )
        return (
            self.config.execution_mode == "command"
            and (self.config.repo_path / "generate.py").exists()
            and self.config.ckpt_dir.exists()
            and self.config.wav2vec_dir.exists()
        )

    def _musetalk_missing_files(self) -> list[str]:
        required = [
            self.config.musetalk_python,
            self.config.musetalk_repo_path / "scripts" / "inference.py",
            self.config.musetalk_model_dir / "musetalkV15" / "unet.pth",
            self.config.musetalk_model_dir / "musetalkV15" / "musetalk.json",
            self.config.musetalk_model_dir / "whisper" / "pytorch_model.bin",
            self.config.musetalk_model_dir / "dwpose" / "dw-ll_ucoco_384.pth",
            self.config.musetalk_model_dir
            / "sd-vae"
            / "diffusion_pytorch_model.bin",
            self.config.musetalk_model_dir / "face-parse-bisent" / "79999_iter.pth",
        ]
        return [str(path) for path in required if not path.exists()]

    def _latest_video(self) -> Path | None:
        videos = sorted(
            list(self.config.video_save_path.glob("*.mp4"))
            + list(self.config.video_save_path.glob("*.webm")),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        return videos[0] if videos else None

    def _video_duration(self, path: Path, text: str) -> float:
        ffprobe = self.config.musetalk_python.parent / "ffprobe"
        try:
            completed = subprocess.run(
                [
                    str(ffprobe),
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=nw=1:nk=1",
                    str(path),
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=15,
                shell=False,
            )
            return round(float(completed.stdout.strip()), 2)
        except (OSError, subprocess.SubprocessError, ValueError):
            return round(max(2.5, len(text) / 5.2), 1)

    def _command_env(self) -> dict[str, str]:
        env = os.environ.copy()
        device_index = (
            self.config.device.split(":")[-1]
            if ":" in self.config.device
            else self.config.device
        )
        env.setdefault("CUDA_VISIBLE_DEVICES", device_index)
        env.setdefault("USE_CHANNELS_LAST_3D", "1")
        env["PATH"] = f"{self.config.musetalk_python.parent}:{env.get('PATH', '')}"
        env.update(self.kernel_runtime.command_environment())
        return env

    def _provider_name(self) -> str:
        if self.config.execution_mode == "musetalk":
            return "MuseTalk 1.5（CUDA）+ Edge TTS"
        if self.config.execution_mode == "command":
            return "SoulX-LiveAct"
        return "数字人本地演示适配器"

    @staticmethod
    def _safe_name(value: str) -> str:
        safe = re.sub(r"[^A-Za-z0-9_-]+", "-", value).strip("-")
        return safe[:80] or "session"
