# 本地真实数字人独立服务

该服务是主 FastAPI 后端与 GPU 数字人推理环境之间的隔离层。当前本机默认使用 **MuseTalk 1.5 + Edge TTS**：先把中文教学文本合成为语音，再在 WSL2 中使用 RTX 4060 生成与语音同步的导师嘴型视频。

## 当前运行模式

```text
前端 DigitalHumanWorkspace
  -> 主后端 /api/digital-human/speak
  -> WSL2 独立服务 :8090/speak
  -> Edge TTS 中文语音
  -> MuseTalk 1.5 CUDA 嘴型推理
  -> /generated-videos/*.mp4
  -> 前端 video 播放器
```

本机配置：

- WSL2：Ubuntu
- GPU：NVIDIA GeForce RTX 4060 Laptop GPU
- PyTorch：2.0.1 + CUDA 11.8
- MuseTalk：1.5
- TTS：Edge TTS，默认 `zh-CN-XiaoxiaoNeural`
- 输出：H.264 + AAC MP4

## 启动

先在项目根目录启动数字人服务：

```powershell
cd D:\cc项目\ai+medicine
.\start-digital-human.ps1
```

再分别启动主后端和前端。健康检查：

```text
GET http://127.0.0.1:8090/health
GET http://127.0.0.1:8000/api/digital-human/modes
```

当 `ready_for_liveact=true` 且 `liveact_available=true` 时，网页的“真实数字人”按钮可用。

## API

- `GET /health`：检查模型、头像、CUDA 和辅助权重。
- `GET /kernel-health`：检查 PyTorch、CUTLASS 和 LightX2V 可选加速条件。
- `POST /speak`：接收教学文本，返回实际生成的 `video_url`。
- `POST /status`：同步待机、倾听、讲解、风险和评分状态。
- `GET /generated-videos/{name}`：读取生成的 MP4。

## 环境变量

`env/.env` 中的主要配置：

```env
DIGITAL_HUMAN_MODE=liveact
LIVEACT_EXECUTION_MODE=musetalk
LIVEACT_REQUEST_TIMEOUT=180
MUSETALK_REPO_PATH=/home/zojer/ai-avatar/MuseTalk
MUSETALK_PYTHON=/home/zojer/ai-avatar/env/bin/python
MUSETALK_MODEL_DIR=/home/zojer/ai-avatar/MuseTalk/models
MUSETALK_RUNTIME_DIR=/home/zojer/ai-avatar/runtime
MUSETALK_AVATAR_IMAGE=/mnt/d/cc项目/ai+medicine/图片/教学数字人.png
MUSETALK_TTS_VOICE=zh-CN-XiaoxiaoNeural
```

模型权重位于 WSL 用户目录，不复制进项目，也不提交版本库。

## 能力边界

当前实现是真实 GPU 嘴型同步，不是 CSS 动画，也不是预录视频；但它仍是离线生成模式，不是 WebRTC 实时流。MuseTalk 主要重绘面部口型，不会自动生成自然的头部、眼神和手势动作。要实现低延迟全身驱动，需要单独部署 SoulX-LiveAct、音频流队列、WebSocket/WebRTC 和更高显存的 GPU。

在本机 RTX 4060 上，已验证 1280×720、25 FPS、约 6 秒中文视频可成功生成；UNet 推理约 13 FPS，包含模型加载、TTS 和预处理的端到端等待约 30–60 秒。

## SoulX、CUTLASS 与 LightX2V

`LIVEACT_EXECUTION_MODE=command` 仍保留 SoulX-LiveAct 命令适配。CUTLASS 与 LightX2V kernel 是底层推理加速组件，不是数字人模型。当前 MuseTalk 使用兼容的 PyTorch CUDA 路径；未配置可选 kernel 不影响生成。

## 安全

- 只使用虚拟导师素材，不使用真实患者照片。
- 不允许前端传入任意命令。
- `audio_url` 只接受已经存在的本地文件，避免远程地址注入。
- 推理失败自动回退本地演示，不中断医学训练流程。
- 所有内容仅用于医学教育训练，不用于真实临床诊断。
