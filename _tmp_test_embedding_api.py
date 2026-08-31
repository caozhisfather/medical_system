import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

env_path = Path(r"E:\18_本科计算机专业课程笔记\07_竞赛\全球人工智能算法精英赛\medical_system-2026-7-31-demo\medical_system-2026-7-31-demo\env\.env")
config = {}
for line in env_path.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    config[k.strip('"')] = v.strip('"').strip("'")

base_url = config.get("OPENAI_BASE_URL", "https://api.deepseek.com").rstrip("/")
api_key = config.get("OPENAI_API_KEY", "")
model = "deepseek-embedding"

body = json.dumps({"model": model, "input": ["右心房", "左心室"], "encoding_format": "float"}, ensure_ascii=False).encode("utf-8")
req = Request(
    f"{base_url}/v1/embeddings",
    data=body,
    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    method="POST",
)
try:
    with urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    embeddings = payload.get("data", [])
    print("EMBEDDING_OK")
    print("COUNT=" + str(len(embeddings)))
    if embeddings:
        print("DIM=" + str(len(embeddings[0].get("embedding", []))))
except Exception as e:
    print("EMBEDDING_ERROR=" + str(e))
