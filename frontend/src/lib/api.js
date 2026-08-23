// API 层：结果集多版本化 + 在线推理。v1 前端只消费 baseline；v2 切 version 即可
const BASE = ''

async function get(path, params = {}) {
  const qs = new URLSearchParams(params).toString()
  const url = `${BASE}${path}${qs ? '?' + qs : ''}`
  const r = await fetch(url)
  if (!r.ok) throw new Error(`${path} → ${r.status}`)
  return r.json()
}

async function post(path, body) {
  const r = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!r.ok) {
    const detail = await r.json().then(j => j.detail).catch(() => '')
    throw new Error(`${path} → ${r.status}${detail ? ': ' + detail : ''}`)
  }
  return r.json()
}

export const api = {
  health: () => get('/api/health').then(d => ({ ok: true, ...d })),
  results: () => get('/api/results'),
  metrics: (version = 'baseline') => get('/api/metrics', { version }),
  segments: (version = 'baseline') => get('/api/segments', { version }).then(d => d.segments),
  frames: (version = 'baseline', limit = 200, offset = 0) =>
    get('/api/frames', { version, limit, offset }).then(d => d.frames),
  buttonFreq: (version = 'baseline') => get('/api/button-freq', { version }),
  demo: (version = 'baseline') => get('/api/demo', { version }).then(d => d.demo),
  comparison: () => get('/api/comparison').then(d => d.frames),
  // 在线推理
  inferStatus: () => get('/api/infer/status'),
  predict: (fid, k = 1, assetId = null, sec = null) =>
    post('/api/predict', { fid, k, asset_id: assetId, sec }),
  evaluate: (n = 200, k = 3, save = false, label = '微调后（ft）', assetId = null, fids = null, result = null) =>
    post('/api/evaluate', { n, k, save, label, asset_id: assetId, fids, result }),
  // 素材评测工作台
  assets: () => get('/api/assets').then(d => d.assets),
  createAsset: (name) => post('/api/assets', { name }).then(d => d.asset_id),
  uploadVideo: (aid, file) => upload(`/api/assets/${aid}/video`, file),
  uploadActions: (aid, file) => upload(`/api/assets/${aid}/actions`, file),
  uploadActionsDir: async (aid, files) => {
    // 文件夹上传：files 为选中文件夹里的文件列表，逐个追加（浏览器会带相对路径 webkitRelativePath）
    const form = new FormData()
    const actionFiles = files.filter(f => f.name === 'actions_processed.parquet')
    if (!actionFiles.length) throw new Error('文件夹中未找到 actions_processed.parquet')
    for (const f of actionFiles) form.append('files', f, f.webkitRelativePath || f.name)
    const r = await fetch(`${BASE}/api/assets/${aid}/actions-dir`, { method: 'POST', body: form })
    if (!r.ok) {
      const detail = await r.json().then(j => j.detail).catch(() => '')
      throw new Error(`actions-dir → ${r.status}${detail ? ': ' + detail : ''}`)
    }
    return r.json()
  },
  extractFrames: (aid, startSec, endSec, fps = 1) =>
    post(`/api/assets/${aid}/frames`, { start_sec: startSec, end_sec: endSec, fps }),
  deleteAsset: (aid) => fetch(`${BASE}/api/assets/${aid}`, { method: 'DELETE' }).then(r => r.json()),
}

async function upload(path, file) {
  const form = new FormData()
  form.append('file', file)
  const r = await fetch(`${BASE}${path}`, { method: 'POST', body: form })
  if (!r.ok) throw new Error(`${path} → ${r.status}`)
  return r.json()
}
