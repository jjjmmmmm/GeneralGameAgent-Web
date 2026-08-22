// API 层：结果集多版本化，v1 前端只消费 baseline；v2 切 version 即可
const BASE = ''

async function get(path, params = {}) {
  const qs = new URLSearchParams(params).toString()
  const url = `${BASE}${path}${qs ? '?' + qs : ''}`
  const r = await fetch(url)
  if (!r.ok) throw new Error(`${path} → ${r.status}`)
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
}
