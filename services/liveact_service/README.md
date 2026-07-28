# SoulX-LiveAct 独立适配服务

该目录是“临思智训”与 [SoulX-LiveAct 官方仓库](https://github.com/Soul-AILab/SoulX-LiveAct) 之间的隔离层。主后端不会导入 CUDA、Torch、wav2vec 或模型权重，也不会在普通启动流程中执行重型推理。

## 默认模式

默认 `LIVEACT_EXECUTION_MODE=mock`。服务返回与真实推理一致的数据结构，前端使用用户提供的虚拟医生导师图和状态动画完成演示。

```powershell
.\.venv\Scripts\python.exe -m uvicorn services.liveact_service.server:app --host 127.0.0.1 --port 8090
```

健康检查：`GET http://127.0.0.1:8090/health`

## 真实推理规划

1. 在独立目录克隆官方仓库，不要复制进本项目。
2. 按官方 README 创建 Python 3.10 Conda 环境并安装依赖、SageAttention、vLLM 与 LightVAE。
3. 单独下载 SoulX-LiveAct checkpoint 和 `chinese-wav2vec2-base`。
4. 配置 `LIVEACT_REPO_PATH`、`LIVEACT_CKPT_DIR` 和 `LIVEACT_WAV2VEC_DIR`。
5. 将 `LIVEACT_EXECUTION_MODE` 改为 `command`，并根据显卡配置 FP8 KV cache、block offload 和 T5 CPU。
6. 对照当前检出的官方 `examples/example.json`，在 `build_input_json()` 中完成稳定业务字段到官方输入字段的最终映射。

官方 README 说明：两张 H100/H200 可在 720x416 或 512x512 下达到约 20 FPS；RTX 4090/5090 可使用 FP8 KV cache、block offload 和 T5 CPU，但速度和质量会下降。真实性能取决于显卡、显存、模型版本和输入长度。

## 许可证注意事项

截至本项目接入时，官方仓库首页未显示明确的根目录 LICENSE 文件。正式比赛发布、商业部署或分发模型权重前，必须再次确认代码、模型和演示素材各自的许可证与使用范围。

## 安全边界

- 不上传真实患者影像或照片。
- 不提交模型权重、生成视频和临时音频。
- 不允许由前端传入任意命令。
- 命令模式使用参数数组并关闭 shell，失败后自动回退 mock。
## CUTLASS 与 LightX2V kernel 加速

数字人独立服务已增加可选 GPU 算子加速层。`GET /kernel-health` 会探测显卡、PyTorch、CUDA、CUTLASS、LightX2V kernel 和 NVFP4 条件，并根据 `LIVEACT_KERNEL_BACKEND=auto|torch|lightx2v` 选择后端。任何条件不满足时都会回退到 PyTorch 兼容路径或本地演示，不影响主网站运行。

这两个仓库是底层推理加速组件，不是数字人生成模型。真实数字人仍需要 SoulX-LiveAct 仓库、模型权重和 wav2vec。由于 CUTLASS 官方说明当前 Windows 构建不可用，推荐在 Ubuntu/WSL2 的独立 GPU 环境部署。完整步骤见 [`docs/digital-human-gpu-acceleration.md`](../../docs/digital-human-gpu-acceleration.md)。

- [NVIDIA CUTLASS](https://github.com/NVIDIA/cutlass/)
- [LightX2V kernel README](https://github.com/ModelTC/LightX2V/blob/main/lightx2v_kernel/README.md)
