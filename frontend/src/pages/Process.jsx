import { useEffect, useRef, useState } from 'react'
import { Link, Navigate, useNavigate, useParams } from 'react-router-dom'
import { ImageUp, Play, RotateCcw } from 'lucide-react'
import { apiUrl, processImage } from '../api/client.js'
import { useImage } from '../context/ImageContext.jsx'
import { ALGORITHM_ORDER, ALGORITHMS, DEFAULT_PARAMS } from '../content/algorithms.js'
import ParamControls from '../components/ParamControls.jsx'
import ResultView from '../components/ResultView.jsx'
import { ErrorBanner, LoadingOverlay } from '../components/common.jsx'

const PARAM_STORE = 'leafguard-params-v1'

function loadParams(algorithm) {
  try {
    const saved = JSON.parse(sessionStorage.getItem(PARAM_STORE) || '{}')
    return { ...DEFAULT_PARAMS[algorithm], ...(saved[algorithm] || {}) }
  } catch {
    return { ...DEFAULT_PARAMS[algorithm] }
  }
}

function saveParams(algorithm, params) {
  try {
    const saved = JSON.parse(sessionStorage.getItem(PARAM_STORE) || '{}')
    sessionStorage.setItem(PARAM_STORE, JSON.stringify({ ...saved, [algorithm]: params }))
  } catch {
    /* ignore */
  }
}

export default function Process() {
  const { algorithm } = useParams()
  const valid = ALGORITHM_ORDER.includes(algorithm)
  if (!valid) return <Navigate to="/algorithms" replace />
  return <ProcessPage key={algorithm} algorithm={algorithm} />
}

function ProcessPage({ algorithm }) {
  const { image, results, setResult } = useImage()
  const navigate = useNavigate()
  const info = ALGORITHMS[algorithm]
  const [params, setParams] = useState(() => loadParams(algorithm))
  const [maxSide, setMaxSide] = useState(() => results[algorithm]?.params?.max_side ?? 400)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const resultRef = useRef(null)
  const result = results[algorithm]

  useEffect(() => saveParams(algorithm, params), [algorithm, params])

  if (!image) {
    return (
      <div className="card mx-auto max-w-lg space-y-4 p-8 text-center">
        <h1 className="text-xl font-semibold text-slate-900">{info.name}</h1>
        <p className="text-sm text-slate-600">Upload a leaf image first - every algorithm processes the original upload.</p>
        <Link to={`/upload?next=${algorithm}`} className="btn-primary">
          <ImageUp size={16} /> Upload image
        </Link>
      </div>
    )
  }

  async function run() {
    setBusy(true)
    setError('')
    try {
      const response = await processImage(algorithm, image.image_id, { ...params, max_side: maxSide })
      setResult(algorithm, response)
      setTimeout(() => resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 50)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-8">
      {/* algorithm switcher */}
      <div className="flex flex-wrap gap-2">
        {ALGORITHM_ORDER.map((key) => (
          <button
            key={key}
            type="button"
            onClick={() => navigate(`/process/${key}`)}
            className={`rounded-xl px-3 py-2 text-sm font-medium transition ${
              key === algorithm ? 'bg-leaf-800 text-white shadow' : 'bg-white text-slate-600 ring-1 ring-slate-200 hover:ring-leaf-700'
            }`}
          >
            {ALGORITHMS[key].name}
            {results[key] && <span className="ml-1.5 text-xs opacity-80">✓</span>}
          </button>
        ))}
      </div>

      <div>
        <h1 className="text-2xl font-bold text-slate-900">{info.name}</h1>
        <p className="text-sm text-slate-500">{info.short} Input: the original upload <b>{image.filename}</b>.</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,22rem)_minmax(0,1fr)]">
        <aside className="card h-fit space-y-5 p-5 lg:sticky lg:top-20">
          <h2 className="font-semibold text-slate-900">Parameters</h2>
          <ParamControls algorithm={algorithm} params={params} onChange={setParams} maxSide={maxSide} onMaxSide={setMaxSide} />
          <div className="flex gap-2">
            <button type="button" className="btn-primary flex-1" onClick={run} disabled={busy}>
              <Play size={16} /> {result ? 'Run again' : 'Run algorithm'}
            </button>
            <button
              type="button"
              className="btn-secondary"
              title="Reset parameters to defaults"
              onClick={() => {
                setParams({ ...DEFAULT_PARAMS[algorithm] })
                setMaxSide(400)
              }}
            >
              <RotateCcw size={16} />
            </button>
          </div>
          <ErrorBanner message={error} onClose={() => setError('')} />
        </aside>

        <section className="relative">
          {busy && <LoadingOverlay text={`Running ${info.name} on the original image…`} />}
          <div className="card overflow-hidden">
            <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3">
              <span className="text-sm font-medium text-slate-700">Input: original uploaded image</span>
              <span className="text-xs text-slate-500">
                {image.width} × {image.height} px (processed at ≤ {maxSide} px)
              </span>
            </div>
            <div className="checkerboard">
              <img src={apiUrl(image.original_url)} alt="Original leaf" className="mx-auto max-h-[26rem] object-contain" />
            </div>
          </div>
          {!result && !busy && (
            <p className="mt-4 rounded-xl bg-leaf-50 p-4 text-sm text-leaf-900">
              Not processed yet. Adjust the parameters and press <b>Run algorithm</b>.
            </p>
          )}
        </section>
      </div>

      <div ref={resultRef} className="scroll-mt-20">
        {result && <ResultView result={result} />}
      </div>
    </div>
  )
}
