# API 接入清单

本清单按当前“人体解剖学习平台”的主线整理。密钥统一放在 `env/.env`，不要写入前端代码或提交到 Git。

## 一、演示前优先接入

| 能力 | 当前调用位置 | 需要配置 | 未接入时表现 | 建议优先级 |
| --- | --- | --- | --- | --- |
| SMTP 邮件 | 注册验证、重发验证、找回密码 | `MAIL_HOST`、`MAIL_PORT`、`MAIL_USERNAME`、`MAIL_PASSWORD`、`PUBLIC_FRONTEND_URL` | 演示账号可登录；新注册账号无法收到验证与重置邮件 | P0 |
| 大语言模型（OpenAI 兼容） | 实时出题、虚拟病人对话、教材证据组织讲解 | `OPENAI_API_KEY`、`OPENAI_BASE_URL`、`OPENAI_MODEL`、`OPENAI_ANSWER_MODEL`、`OPENAI_MAX_TOKENS` | 解剖测验使用本地题库；虚拟病人使用规则兜底；教材证据仍会展示，但不生成模型补充段 | P0 |
| Embedding 向量化 | 教材检索、教学知识入库、RAG 召回 | `EMBEDDING_API_KEY`、`EMBEDDING_BASE_URL`、`EMBEDDING_MODEL` | 使用已有本地索引；新增资料无法获得线上向量 | P0 |
| 解剖 Agent 的可选 LLM 增强 | `POST /api/agent/chat` 的 `anatomy_lab` 分支，由 `AnatomyTutor` 处理 | 当前无需 LLM API；后续生成式讲解或工具选择需新增受控适配器，可复用 OpenAI 兼容配置 | 当前为本地有界 Skill 编排，最多调用三个管理员批准的只读工具，返回教材依据和实际调用状态 | P2 |
| TTS 语音合成 | 数字人和讲解语音 | 需要实现具体供应商适配器，再配置 `TTS_PROVIDER`、供应商密钥和 `TTS_VOICE` | `/api/tts/speak` 仅返回模拟状态，不返回音频 | P1 |

## 二、增强能力

| 能力 | 当前调用位置 | 需要配置 | 未接入时表现 | 建议优先级 |
| --- | --- | --- | --- | --- |
| 视觉模型（OpenAI 兼容） | 教学资料图片识别、病例资料视觉解析 | `QWEN_VISION_API_KEY`、`QWEN_VISION_BASE_URL`、`QWEN_VISION_MODEL` | 视觉解析不可用，不影响三维解剖 | P2 |
| 讯飞星火 SparkOS | 音频对话、可选智能体通道 | `LLM_APPID`、`LLM_APIKEY`、`LLM_APISECRET`、`LLM_WS_URL`、`LLM_SCENE` | 使用普通文本智能体链路 | P2 |
| 数字人 LiveAct 服务 | 数字人视频驱动 | `LIVEACT_SERVICE_URL`、`LIVEACT_AVATAR_ID`、`DIGITAL_HUMAN_MODE` | 显示内置模拟视频或静态状态 | P2 |
| 外部 RAG 服务 | 可选的机构知识库检索 | `RAG_URL`、`RAG_APIPWD`、`RAG_PROVIDER` | 使用本地 JSON/向量索引 | P2 |
| Milvus | 大规模向量检索 | `MILVUS_URI`，或 `MILVUS_HOST` + `MILVUS_PORT` | 使用本地 Chroma/文件索引 | P2 |

## 三、生产部署需要替换的内部接口

这些不是第三方模型 API，但当前主要是本地演示实现，上线前需要接入正式服务：

| 模块 | 当前状态 | 正式环境需要 |
| --- | --- | --- |
| 登录与用户 | SQLite、PBKDF2 密码哈希、一次性邮件令牌、服务端会话 | 学校统一认证或正式用户服务、共享会话存储、集中限流、备份与审计 |
| 学习记录 | 本地 JSON 文件 | 数据库、用户隔离、备份与审计 |
| 教师知识库 | 本地 JSON 和本地处理任务 | 对象存储、任务队列、数据库、文档权限 |
| 解剖图谱维护 | 启动时由 `atlas.json`、`organs.json` 和术语表构建 | 图谱数据库或后台编辑 API、版本管理、教师审核 |
| 考试题库 | 本地运行时缓存 | 持久化题库、考试发布、作答记录、防重复提交 |
| 审计日志 | 本地 JSONL | 集中式审计存储、访问控制与留存策略 |
| Skill 配置与调用记录 | 本地 SQLite，服务端会话鉴权、角色授权、每账号小时额度 | 共享生产存储、请求限流、记录留存策略、配置并发版本控制 |

## 四、当前不需要申请 API 的资源

- BodyParts3D 三维模型作为本地静态资源加载，不需要远程 API。
- 本地《系统解剖学》索引和术语表不需要远程 API。
- 逐页教材证据、原始页图渲染和按“文档 + 页码”保存的学生笔记使用本地 OCR/PDF 与用户数据，不需要额外第三方 API；检索结果可通过 `GET /api/anatomy/evidence`、`GET /api/anatomy/textbook/page` 和 `/api/anatomy/notes` 验证。
- `anatomy_search`、`textbook_search`、`graph_query` 是本地预置 Skill，首次启动默认关闭，由管理员在 `/admin/skills` 启用并授权；不依赖外部 LLM 工具选择，教材语义检索可能沿用现有 Embedding 服务。详见 [Skill 与解剖导师](SKILL_AGENT_SETUP.md)。
- Wikimedia/OpenStax/B 站资源目前使用公开链接，不需要 API Key，但正式发布前必须继续做版权、可用性和内容审核。

## 五、最小配置示例

```dotenv
MAIL_HOST=smtp.163.com
MAIL_PORT=465
MAIL_USERNAME=
MAIL_PASSWORD=
PUBLIC_FRONTEND_URL=http://127.0.0.1:5173

OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com
OPENAI_MODEL=gpt-4.1
OPENAI_ANSWER_MODEL=
OPENAI_MAX_TOKENS=2800

EMBEDDING_API_KEY=
EMBEDDING_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode
EMBEDDING_MODEL=text-embedding-v3

TTS_PROVIDER=placeholder
DIGITAL_HUMAN_MODE=mock
RAG_PROVIDER=local
```

接入后先访问 `GET /api/health` 检查配置状态，再分别验证实时出题、AnatomyAgent、`GET /api/anatomy/evidence`、`GET /api/anatomy/textbook/page`、逐页笔记和数字人链路。
