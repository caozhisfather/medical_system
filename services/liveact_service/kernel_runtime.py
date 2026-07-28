from __future__ import annotations

import importlib.util
import os
import platform
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name, str(default)).strip().lower()
    return value in {"1", "true", "yes", "on"}


def _version_tuple(value: str) -> tuple[int, ...]:
    match = re.search(r"\d+(?:\.\d+)+", value)
    if not match:
        return ()
    return tuple(int(part) for part in match.group(0).split("."))


@dataclass(frozen=True)
class KernelRuntimeConfig:
    requested_backend: str = os.getenv("LIVEACT_KERNEL_BACKEND", "auto").strip().lower()
    cutlass_path: Path = Path(os.getenv("CUTLASS_PATH", ""))
    lightx2v_path: Path = Path(os.getenv("LIGHTX2V_PATH", ""))
    lightx2v_kernel_wheel: Path = Path(os.getenv("LIGHTX2V_KERNEL_WHEEL", ""))
    lightx2v_kernel_module: str = os.getenv("LIGHTX2V_KERNEL_MODULE", "lightx2v_kernel").strip()
    minimum_torch_version: str = os.getenv("LIGHTX2V_MIN_TORCH_VERSION", "2.7").strip()
    enable_nvfp4: bool = _env_flag("LIVEACT_ENABLE_NVFP4")
    cuda_arch: str = os.getenv("LIVEACT_CUDA_ARCH", "").strip()


class KernelRuntimeProbe:
    """Reports optional CUTLASS/LightX2V acceleration without making it a hard dependency."""

    def __init__(self, config: KernelRuntimeConfig | None = None) -> None:
        self.config = config or KernelRuntimeConfig()

    def status(self) -> dict[str, Any]:
        torch_info = self._torch_status()
        gpu_info = self._gpu_status(torch_info)
        cutlass_configured = self._cutlass_configured()
        lightx2v_source_configured = self._lightx2v_source_configured()
        kernel_module_installed = bool(
            self.config.lightx2v_kernel_module
            and importlib.util.find_spec(self.config.lightx2v_kernel_module)
        )
        wheel_configured = self._file_configured(self.config.lightx2v_kernel_wheel)
        is_linux = platform.system().lower() == "linux"
        torch_version_ok = bool(
            torch_info["installed"]
            and _version_tuple(str(torch_info["version"]))
            >= _version_tuple(self.config.minimum_torch_version)
        )
        cuda_ready = bool(torch_info["cuda_available"])
        compute_capability = str(gpu_info.get("compute_capability") or "")
        nvfp4_hardware_ready = self._supports_nvfp4(compute_capability)
        lightx2v_ready = bool(
            is_linux
            and torch_version_ok
            and cuda_ready
            and cutlass_configured
            and kernel_module_installed
        )
        nvfp4_ready = bool(lightx2v_ready and nvfp4_hardware_ready and self.config.enable_nvfp4)
        selected_backend = self._select_backend(lightx2v_ready)

        notes: list[str] = []
        if not is_linux:
            notes.append("CUTLASS 4.x/3.x 官方说明当前 Windows 构建不可用，建议在 Ubuntu 或 WSL2 的独立推理服务中部署。")
        if not torch_info["installed"]:
            notes.append(f"未安装 PyTorch；LightX2V kernel 要求 PyTorch >= {self.config.minimum_torch_version}。")
        elif not torch_version_ok:
            notes.append(f"PyTorch 版本低于 LightX2V kernel 要求的 {self.config.minimum_torch_version}。")
        if not cutlass_configured:
            notes.append("未配置 CUTLASS_PATH，当前不会编译或加载 CUTLASS 算子。")
        if not kernel_module_installed:
            notes.append("未检测到 LightX2V kernel 模块，数字人服务将使用兼容路径。")
        if self.config.enable_nvfp4 and not nvfp4_hardware_ready:
            notes.append("当前显卡架构不满足本项目的 NVFP4 启用条件，已自动关闭该路径。")
        if not notes:
            notes.append("CUTLASS 与 LightX2V kernel 加速环境已就绪。")

        return {
            "status": "ready" if lightx2v_ready else "fallback",
            "requested_backend": self.config.requested_backend,
            "selected_backend": selected_backend,
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "torch": torch_info,
            "gpu": gpu_info,
            "cutlass": {
                "configured": cutlass_configured,
                "path": str(self.config.cutlass_path) if cutlass_configured else "",
            },
            "lightx2v_kernel": {
                "source_configured": lightx2v_source_configured,
                "wheel_configured": wheel_configured,
                "module": self.config.lightx2v_kernel_module,
                "module_installed": kernel_module_installed,
                "minimum_torch_version": self.config.minimum_torch_version,
                "ready": lightx2v_ready,
            },
            "nvfp4": {
                "requested": self.config.enable_nvfp4,
                "hardware_ready": nvfp4_hardware_ready,
                "ready": nvfp4_ready,
            },
            "notes": notes,
        }

    def command_environment(self) -> dict[str, str]:
        status = self.status()
        return {
            "LIVEACT_KERNEL_BACKEND": str(status["selected_backend"]),
            "LIVEACT_ENABLE_NVFP4": "1" if status["nvfp4"]["ready"] else "0",
            "CUTLASS_PATH": str(self.config.cutlass_path) if self._cutlass_configured() else "",
            "LIGHTX2V_PATH": str(self.config.lightx2v_path) if self._lightx2v_source_configured() else "",
        }

    def _select_backend(self, lightx2v_ready: bool) -> str:
        requested = self.config.requested_backend
        if requested not in {"auto", "torch", "lightx2v"}:
            requested = "auto"
        if requested == "lightx2v":
            return "lightx2v" if lightx2v_ready else "torch"
        if requested == "auto":
            return "lightx2v" if lightx2v_ready else "torch"
        return "torch"

    def _torch_status(self) -> dict[str, Any]:
        if importlib.util.find_spec("torch") is None:
            return {
                "installed": False,
                "version": "",
                "cuda_available": False,
                "cuda_version": "",
            }
        try:
            import torch

            return {
                "installed": True,
                "version": str(torch.__version__),
                "cuda_available": bool(torch.cuda.is_available()),
                "cuda_version": str(torch.version.cuda or ""),
            }
        except (ImportError, OSError, RuntimeError) as exc:
            return {
                "installed": False,
                "version": "",
                "cuda_available": False,
                "cuda_version": "",
                "error": f"{type(exc).__name__}: {exc}",
            }

    def _gpu_status(self, torch_info: dict[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] = {
            "available": False,
            "name": "",
            "compute_capability": self.config.cuda_arch,
            "driver_version": "",
            "memory_total_mib": None,
            "nvcc_available": shutil.which("nvcc") is not None,
        }
        if torch_info["installed"] and torch_info["cuda_available"]:
            try:
                import torch

                capability = torch.cuda.get_device_capability(0)
                result.update(
                    {
                        "available": True,
                        "name": torch.cuda.get_device_name(0),
                        "compute_capability": f"{capability[0]}.{capability[1]}",
                    }
                )
                return result
            except (OSError, RuntimeError):
                pass

        nvidia_smi = shutil.which("nvidia-smi")
        if not nvidia_smi:
            return result
        try:
            completed = subprocess.run(
                [
                    nvidia_smi,
                    "--query-gpu=name,compute_cap,memory.total,driver_version",
                    "--format=csv,noheader,nounits",
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=3,
                shell=False,
            )
            first_line = completed.stdout.strip().splitlines()[0]
            name, capability, memory, driver = [part.strip() for part in first_line.split(",", 3)]
            result.update(
                {
                    "available": True,
                    "name": name,
                    "compute_capability": capability,
                    "driver_version": driver,
                    "memory_total_mib": int(float(memory)),
                }
            )
        except (OSError, subprocess.SubprocessError, TimeoutError, ValueError, IndexError):
            pass
        return result

    def _cutlass_configured(self) -> bool:
        path = self.config.cutlass_path
        return bool(str(path)) and (path / "include" / "cutlass").is_dir()

    def _lightx2v_source_configured(self) -> bool:
        path = self.config.lightx2v_path
        return bool(str(path)) and (path / "lightx2v_kernel").is_dir()

    @staticmethod
    def _file_configured(path: Path) -> bool:
        return bool(str(path)) and path.is_file()

    @staticmethod
    def _supports_nvfp4(compute_capability: str) -> bool:
        match = re.match(r"(\d+)(?:\.(\d+))?", compute_capability)
        return bool(match and int(match.group(1)) >= 10)
