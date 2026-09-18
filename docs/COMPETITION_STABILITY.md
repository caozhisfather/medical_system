# 比赛稳定版运行手册

本项目的比赛主线是：三维解剖结构选择 → 结构高亮 → 教材依据 → 知识图谱 → 针对结构出题 → 服务端判分 → 复习建议。

## 现场启动

在项目根目录打开 PowerShell：

```powershell
$env:PYTHONUTF8 = "1"
(& (Get-Command conda.exe).Source "shell.powershell" "hook") | Out-String | Invoke-Expression
conda activate pytorch_env
.\scripts\start-project.ps1
.\scripts\verify-project.ps1
```

启动脚本会：

- 固定使用 `pytorch_env`；
- 使用本地解剖数据、教材索引和知识图谱；
- 设置 `DEMO_MODE=true`；
- 设置 `TTS_PROVIDER=placeholder`、`DIGITAL_HUMAN_MODE=mock` 的本地兜底；
- 关闭后端热重载，避免比赛过程中扫描文件造成重启；
- 将日志写入 `runtime/logs/`。

访问地址：

- 前端：`http://127.0.0.1:5173/`
- 学生演示：`http://127.0.0.1:5173/student/dashboard?demo=student`
- 后端健康检查：`http://127.0.0.1:8000/api/health`
- API 文档：`http://127.0.0.1:8000/docs`

## 现场验收

`verify-project.ps1` 会检查：

- 当前 Conda 环境是否为 `pytorch_env`；
- 后端健康状态和关键数据是否就绪；
- 是否启用比赛离线演示模式；
- 前端入口是否返回 200；
- 解剖练习、术语、教材、图谱和模型清单是否存在；
- 学生演示账号是否可以登录；
- 解剖 API、图谱 API 和教材检索是否可用；
- 模型部件、器官映射、素材图谱和术语表是否相互一致；
- Git 已跟踪文件中是否出现常见密钥模式。

验收失败时优先查看：

```text
runtime/logs/backend-error.log
runtime/logs/frontend-error.log
```

## 重置演示状态

先停止服务，再重置。脚本会把本地认证、Skill、测验和训练状态移动到带时间戳的备份目录，不会直接删除：

```powershell
.\scripts\stop-project.ps1
.\scripts\reset-demo-data.ps1
.\scripts\start-project.ps1
.\scripts\verify-project.ps1
```

如果需要保留现有账号：

```powershell
.\scripts\reset-demo-data.ps1 -KeepAuth
```

## 黄金演示流程

1. 使用学生演示账号登录。
2. 进入“三维解剖训练”。
3. 选择心脏、肺或胃等器官。
4. 点选精细结构，确认模型高亮。
5. 打开“教材详解”，展示章节和页码依据。
6. 打开“空间关系”或图谱入口，展示结构关系。
7. 针对当前结构出题。
8. 提交答案，展示服务器端判分和错误反馈。
9. 回到学习档案，展示复习记录。

比赛现场不把 SMTP、外部 LLM、远程 Embedding、数字人或语音服务作为主流程依赖。它们属于可选增强能力，主流程必须在断网情况下完成。

## 发布前清单

- [ ] 技术方案、演示视频和答辩材料不包含学校名称、Logo 或指导教师信息。
- [ ] 三维模型、图片、教材和外部链接均有署名与授权记录。
- [ ] 作品简介控制在 300 字以内，技术方案正文控制在 8000 字以内。
- [ ] 演示视频为 MP4，时长 3-5 分钟，大小不超过 300 MB。
- [ ] 现场设备支持 WebGL，浏览器已允许本地服务访问。
- [ ] 断网后再次执行 `verify-project.ps1 -AllowDevelopmentMode`，主流程仍可运行。
- [ ] 连续完成至少 20 次刷新、结构选择、教材弹窗和测验提交，无页面错误。
