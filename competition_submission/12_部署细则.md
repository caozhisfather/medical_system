# 医学资料与知识库部署细则

本文用于把当前项目部署到另一台服务器，并解决以下问题：

- 项目代码已经部署，但本地教材、图谱和指南 PDF 没有上传。
- `data/document_library.json` 中保存的是开发电脑的绝对路径。
- 服务器上的教材检索为空，或返回 `source_unavailable`。
- OCR、向量索引和数据库文件没有一起迁移。

## 一、先理解现有架构

### 1.1 与资料相关的文件

| 文件或目录 | 作用 | 是否提交 Git |
| --- | --- | --- |
| `storage/knowledge_uploads/` | 管理员上传的原始资料 | 否 |
| `data/document_library.json` | 文档登记表，保存标题、页数、路径和处理状态 | 否 |
| `storage/document_ocr/` | 逐页 OCR 文本 | 否 |
| `data/document_embeddings.json` | 向量索引元数据 | 否 |
| `data/document_embeddings.npz` | 向量矩阵 | 否 |
| `data/auth.sqlite3` | 用户和会话 | 否 |
| `data/skills.sqlite3` | Skill 权限和调用记录 | 否 |
| `data/anatomy_learning.sqlite3` | 定位测验与错题记录 | 否 |
| `data/student_notes.json` | 学生笔记和教材勾画 | 否 |

这些文件默认被 `.gitignore` 忽略，因此从 GitHub clone 后不会自动出现。服务器必须单独上传并重建索引。

### 1.2 路径规则

`source_path` 是文档登记表中最重要的字段。

- 开发电脑上可能是 `E:\...\教材.pdf`。
- Linux 服务器上不能继续使用这个 Windows 路径。
- 服务器部署时，应使用 Linux 绝对路径或相对项目根目录的路径。
- 只要服务器上找不到 `source_path` 指向的文件，OCR 会标记为 `source_unavailable`，教材检索就没有结果。

## 二、推荐目录规划

以 Ubuntu 服务器为例：

```text
/opt/medical_system/
├─ medical_system/                  # Git 仓库
│  ├─ backend/
│  ├─ frontend/
│  ├─ data/
│  ├─ storage/
│  ├─ env/.env
│  └─ competition_submission/
└─ materials/                       # 原始资料，建议放在仓库外
   ├─ textbooks/
   ├─ atlases/
   ├─ guidelines/
   └─ other/
```

如果服务器是 Windows，也应使用类似结构，不要依赖 `E:\` 开发盘符。

## 三、上传项目代码

```bash
cd /opt/medical_system
git clone <仓库地址> medical_system
cd medical_system
git checkout 2026-9-17-12th
```

建议部署固定提交：

```bash
git checkout cca9963
```

然后安装依赖：

```bash
conda activate pytorch_env
python -m pip install -r backend/requirements.txt

corepack enable
pnpm --dir frontend install
```

## 四、配置 env/.env

项目只读取 `env/.env`，不是仓库根目录的 `.env`。

```bash
mkdir -p env
cp .env.example env/.env
nano env/.env
```

至少检查以下配置：

```dotenv
FASTAPI_ENV=production
DEMO_MODE=false
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
FRONTEND_ORIGIN=https://你的前端域名
PUBLIC_FRONTEND_URL=https://你的前端域名

OPENAI_API_KEY=你的模型密钥
OPENAI_BASE_URL=你的 OpenAI 兼容接口
OPENAI_MODEL=你的推理模型
OPENAI_ANSWER_MODEL=你的教材讲解模型
OPENAI_MAX_TOKENS=2800

EMBEDDING_API_KEY=你的向量模型密钥
EMBEDDING_BASE_URL=你的兼容接口
EMBEDDING_MODEL=text-embedding-v3
EMBEDDING_TIMEOUT=60

QWEN_VISION_API_KEY=你的视觉 OCR 密钥
QWEN_VISION_BASE_URL=你的视觉模型接口
QWEN_VISION_MODEL=qwen-vl-max

AUTH_DATABASE_PATH=./data/auth.sqlite3
SKILL_DATABASE_PATH=./data/skills.sqlite3
KNOWLEDGE_NOTES_PATH=./data/student_notes.json
ANATOMY_LEARNING_DATABASE_PATH=./data/anatomy_learning.sqlite3
```

注意：

- `OPENAI_ANSWER_MODEL` 不要填一个先消耗大量 reasoning token 的模型，否则可能返回空答案。
- `QWEN_VISION_*` 只对扫描版 PDF 生效。
- `env/.env` 绝对不能提交 Git。

## 五、上传原始医学资料

### 5.1 从本地上传

Windows PowerShell 示例：

```powershell
scp -r "E:\18_本科计算机专业课程笔记\07_竞赛\全球人工智能算法精英赛\教科书籍\书籍" user@server:/opt/medical_system/materials/textbooks
scp -r "E:\18_本科计算机专业课程笔记\07_竞赛\全球人工智能算法精英赛\奈特解剖图谱" user@server:/opt/medical_system/materials/atlases
scp -r "E:\18_本科计算机专业课程笔记\07_竞赛\全球人工智能算法精英赛\全科临床指南中文（中英文本）" user@server:/opt/medical_system/materials/guidelines
```

Linux rsync 示例：

```bash
rsync -av --progress /local/books/ user@server:/opt/medical_system/materials/textbooks/
rsync -av --progress /local/atlases/ user@server:/opt/medical_system/materials/atlases/
rsync -av --progress /local/guidelines/ user@server:/opt/medical_system/materials/guidelines/
```

上传后检查：

```bash
find /opt/medical_system/materials -type f -name '*.pdf' | wc -l
du -sh /opt/medical_system/materials
```

### 5.2 不要只复制 document_library.json

只复制 `data/document_library.json`、但服务器没有原 PDF，结果仍然是：

```text
source_unavailable
```

因为登记表里保存的还是开发电脑的绝对路径。

## 六、把资料登记到服务器数据库

推荐使用管理员上传接口，因为服务器会自动保存成相对路径：

```text
管理员登录
-> 教学知识库
-> 上传资料
-> 选择 textbook / evidence / case
```

如果资料数量很多，使用批量脚本。

### 6.1 批量脚本当前限制

当前脚本：

```text
backend/scripts/import_medical_documents.py
```

顶部有 `SOURCES` 列表。开发版本包含 Windows 绝对路径。Linux 部署前必须改成服务器资料目录。

### 6.2 Linux 推荐改法

在服务器上修改：

```python
SOURCES = [
    (Path("/opt/medical_system/materials/textbooks"), "textbook", "教材"),
    (Path("/opt/medical_system/materials/atlases"), "textbook", "解剖图谱"),
    (Path("/opt/medical_system/materials/guidelines"), "evidence", "临床指南"),
]
```

如果服务器是 Windows：

```python
SOURCES = [
    (Path(r"D:\medical_materials\textbooks"), "textbook", "教材"),
    (Path(r"D:\medical_materials\atlases"), "textbook", "解剖图谱"),
    (Path(r"D:\medical_materials\guidelines"), "evidence", "临床指南"),
]
```

不要继续使用 `E:\18_本科计算机专业课程笔记...` 这样的开发机路径。

### 6.3 重建登记表

先备份旧登记表：

```bash
cp data/document_library.json data/document_library.windows.json.bak
```

如果旧登记表全部是错误路径，删除或在服务器重建：

```bash
python backend/scripts/import_medical_documents.py
```

检查结果：

```bash
python - <<'PY'
import json
from pathlib import Path
data = json.loads(Path("data/document_library.json").read_text("utf-8"))
print("documents=", len(data.get("documents", [])))
for item in data.get("documents", [])[:5]:
    print(item["title"], "|", item["source_path"])
PY
```

每个 `source_path` 必须能在服务器上访问。

## 七、执行 OCR

```bash
conda activate pytorch_env
python backend/scripts/extract_document_text.py
```

输出目录：

```text
storage/document_ocr/
```

状态说明：

| 状态 | 含义 |
| --- | --- |
| `completed` | 已提取文本，可以继续生成向量 |
| `scanned_pdf` | PDF 没有文本层，需要视觉 OCR |
| `source_unavailable` | `source_path` 不存在 |
| `failed` | 文件损坏或 OCR 异常 |

扫描版资料要确认：

```dotenv
QWEN_VISION_API_KEY=...
QWEN_VISION_BASE_URL=...
QWEN_VISION_MODEL=qwen-vl-max
```

如果 OCR 失败，先修复 `source_path` 和视觉模型配置，不要继续生成向量。

## 八、生成向量索引

```bash
python backend/scripts/build_document_embeddings.py
```

可以先小批量验证：

```bash
python backend/scripts/build_document_embeddings.py --limit 2
```

成功后检查：

```bash
python - <<'PY'
import json
from pathlib import Path
meta = json.loads(Path("data/document_embeddings.json").read_text("utf-8"))
print("indexed_items=", len(meta.get("items", [])))
print("model=", meta.get("model"))
PY
```

`indexed_items` 必须大于 0。如果为 0，说明没有生成成功；如果出现 `403 quota exhausted`，需要更换或充值 Embedding 服务。

## 九、迁移已有用户、Skill、测验和笔记

如果比赛部署需要保留本地用户和记录，需要单独复制：

```text
data/auth.sqlite3
data/skills.sqlite3
data/anatomy_learning.sqlite3
data/student_notes.json
```

复制前先停止服务，复制后检查文件权限。

如果只是部署演示环境，可以不复制这些文件：

```bash
python -m backend.app.main
```

后端会创建新的空数据库。

## 十、启动服务

后端：

```bash
conda activate pytorch_env
python -m backend.app.main
```

前端开发验证：

```bash
corepack pnpm --dir frontend dev
```

生产构建：

```bash
corepack pnpm --dir frontend build
```

生产环境建议：

- 前端 `frontend/dist` 交给 Nginx。
- `/api` 反向代理到 `127.0.0.1:8000`。
- SPA 路由回退到 `index.html`。
- 使用 systemd 或 supervisor 守护后端。

## 十一、验证清单

### 11.1 后端健康

```bash
curl http://127.0.0.1:8000/api/health
```

检查：

- `status=ok`
- `readiness=ready`
- `ai.llm_configured=true`
- `embedding` 能正常配置

### 11.2 资料登记

```bash
python - <<'PY'
import json
from pathlib import Path
data = json.loads(Path("data/document_library.json").read_text("utf-8"))
for status in ("completed", "scanned_pdf", "source_unavailable", "failed"):
    count = sum(1 for item in data["documents"] if item.get("ocr_status") == status)
    print(status, count)
PY
```

### 11.3 教材证据检索

```bash
curl "http://127.0.0.1:8000/api/anatomy/evidence?q=心脏&limit=3&with_answer=false"
```

至少应满足：

- `found=true`
- `evidence` 不为空
- 返回页码、行号、文档名称

### 11.4 教材页图片

```bash
curl -I "http://127.0.0.1:8000/api/anatomy/textbook/page?document_id=你的文档ID&page=1"
```

应返回 `200 image/png`。

### 11.5 管理员处理状态

管理员登录后访问：

```text
GET /api/admin/teaching-knowledge/process
GET /api/admin/teaching-knowledge/embeddings/process
```

或者直接使用管理员页面的知识库状态卡片。

## 十二、常见问题

### 检索为空

按顺序检查：

1. 服务器是否有原始 PDF。
2. `source_path` 是否能在服务器访问。
3. OCR 是否完成。
4. `storage/document_ocr/` 是否有对应 JSON。
5. `document_embeddings.json` 的 `items` 是否大于 0。

### 显示 source_unavailable

原因是 `document_library.json` 保存了本地绝对路径。不要在 Windows 上复制数据库后直接上传，应该重新登记服务器路径，或把服务器文件路径更新回登记表。

### Embedding 返回 403

说明向量服务没有额度或 Key 不可用。此时 OCR 仍可做词法检索回退，但不能称为完整向量检索。

### 中文文件名乱码

确保：

- 上传工具使用 UTF-8。
- Linux locale 支持 UTF-8。
- 不要通过会转换编码的旧脚本批量重命名。

### 页面能打开但没有教材页

检查：

- `document_id` 是否存在。
- `page` 是否超过 `page_count`。
- 原始 PDF 是否在服务器上。
- 后端进程对 PDF 文件是否有读取权限。

## 十三、部署完成后的交接

请部署同学最后提供：

- [ ] 服务器代码版本或 Git 提交号
- [ ] 原始资料目录
- [ ] `document_library.json` 资料数量
- [ ] OCR 完成数量
- [ ] 向量索引 items 数量
- [ ] 教材检索验证截图
- [ ] 教材页图片验证截图
- [ ] 管理员知识库状态截图
- [ ] 备份目录
- [ ] 启动、停止和重启命令

## 十四、最小操作顺序

如果只想尽快让服务器恢复教材检索：

```bash
cd /opt/medical_system/medical_system
conda activate pytorch_env

# 1. 上传 PDF 到 /opt/medical_system/materials
# 2. 修改 backend/scripts/import_medical_documents.py 的 SOURCES
python backend/scripts/import_medical_documents.py
python backend/scripts/extract_document_text.py
python backend/scripts/build_document_embeddings.py

# 3. 验证
curl "http://127.0.0.1:8000/api/anatomy/evidence?q=心脏&limit=3&with_answer=false"
```
