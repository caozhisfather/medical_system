const base = import.meta.env.VITE_API_BASE_URL || '';
export async function teaching<T = any>(path: string, method = 'GET', data?: unknown): Promise<T> {
  const token = localStorage.getItem('medical_auth_token');
  const binary = data instanceof File;
  const response = await fetch(`${base}/api/teaching${path}`, {
    method, headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}), ...(data && !binary ? { 'Content-Type': 'application/json' } : {}) },
    body: data === undefined ? undefined : binary ? data : JSON.stringify(data)
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(typeof payload.detail === 'string' ? payload.detail : Array.isArray(payload.detail) ? payload.detail.map((e: {msg: string}) => e.msg).join('；') : `请求失败（${response.status}）`);
  }
  return response.json();
}
export async function teachingDownload(path: string, filename: string) {
  const token = localStorage.getItem('medical_auth_token');
  const response = await fetch(`${base}/api/teaching${path}`, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
  if (!response.ok) { const p = await response.json().catch(() => ({})); throw new Error(p.detail || '下载失败'); }
  const url = URL.createObjectURL(await response.blob());
  const a = document.createElement('a'); a.href = url; a.download = filename; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
