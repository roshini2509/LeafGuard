// All backend calls go through /api (forwarded to FastAPI by the Vite proxy).
export const API_BASE = '/api'

/** Turn a backend path such as "/download/..." into a URL the browser can load. */
export function apiUrl(path) {
  if (!path) return ''
  return path.startsWith('http') ? path : `${API_BASE}${path}`
}

async function readError(response) {
  try {
    const body = await response.json()
    if (typeof body.detail === 'string') return body.detail
    if (Array.isArray(body.detail)) {
      // FastAPI validation errors: [{loc: [...], msg: "..."}]
      return body.detail.map((d) => `${d.loc?.slice(-1)[0] ?? 'value'}: ${d.msg}`).join('; ')
    }
  } catch {
    /* not JSON */
  }
  return `Request failed (${response.status} ${response.statusText})`
}

async function request(path, options = {}) {
  let response
  try {
    response = await fetch(`${API_BASE}${path}`, options)
  } catch {
    throw new Error('Cannot reach the LeafGuard backend. Is it running on port 8000?')
  }
  if (!response.ok) throw new Error(await readError(response))
  return response.json()
}

export function uploadImage(file) {
  const form = new FormData()
  form.append('file', file)
  return request('/upload', { method: 'POST', body: form })
}

export function deleteImage(imageId) {
  return request(`/upload/${imageId}`, { method: 'DELETE' })
}

export function processImage(algorithm, imageId, params) {
  return request(`/process/${algorithm}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ image_id: imageId, ...params }),
  })
}

export function selectClusters(imageId, runId, background, suspected) {
  return request('/process/kmeans/select', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      image_id: imageId,
      run_id: runId,
      background_clusters: background,
      suspected_clusters: suspected,
    }),
  })
}

export function getHsvPresets() {
  return request('/presets/hsv')
}
