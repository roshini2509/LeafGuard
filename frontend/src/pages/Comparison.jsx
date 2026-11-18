import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Clock, ImageUp, Play } from 'lucide-react'
import { apiUrl } from '../api/client.js'
import { useImage } from '../context/ImageContext.jsx'
import { ALGORITHM_ORDER, ALGORITHMS } from '../content/algorithms.js'
import { Lightbox } from '../components/common.jsx'

/** Shows only results that already exist - opening this page never runs an algorithm. */
export default function Comparison() {
  const { image, results } = useImage()
  const [open, setOpen] = useState(null)

  if (!image) {
    return (
      <div className="card mx-auto max-w-lg space-y-4 p-8 text-center">
        <h1 className="text-xl font-semibold">Comparison dashboard</h1>
        <p className="text-sm text-slate-600">Upload an image and run some algorithms to compare their outputs here.</p>
        <Link to="/upload" className="btn-primary">
          <ImageUp size={16} /> Upload image
        </Link>
      </div>
    )
  }

  const displayFor = (key) => {
    const result = results[key]
    if (key === 'kmeans' && result.selection?.overlay) {
      return { ...result.selection.overlay, title: 'K-Means suspected region (approximate)' }
    }
    return result.final
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Comparison dashboard</h1>
        <p className="text-sm text-slate-500">
          Outputs of the algorithms you have run on <b>{image.filename}</b>. Each one processed the same original image
          independently.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,20rem)_minmax(0,1fr)]">
        <figure className="card h-fit overflow-hidden">
          <div className="checkerboard">
            <img src={apiUrl(image.original_url)} alt="Original" className="mx-auto w-full object-contain" />
          </div>
          <figcaption className="p-3 text-sm">
            <div className="font-medium text-slate-900">Original uploaded image</div>
            <div className="text-xs text-slate-500">
              {image.width} × {image.height} px · input to every algorithm
            </div>
          </figcaption>
        </figure>

        <div className="grid gap-5 sm:grid-cols-2">
          {ALGORITHM_ORDER.map((key) => {
            const result = results[key]
            const info = ALGORITHMS[key]
            return (
              <article key={key} className="card flex flex-col overflow-hidden">
                <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3">
                  <h2 className="font-semibold text-slate-900">{info.name}</h2>
                  {result && (
                    <span className="flex items-center gap-1 text-xs text-slate-500">
                      <Clock size={12} /> {(result.time_seconds * 1000).toFixed(0)} ms
                    </span>
                  )}
                </div>
                {result ? (
                  <>
                    <button type="button" className="checkerboard" onClick={() => setOpen(displayFor(key))}>
                      <img src={apiUrl(displayFor(key).url)} alt={displayFor(key).title} className="mx-auto aspect-square w-full object-contain" />
                    </button>
                    <div className="space-y-1 p-4 text-sm">
                      <div className="font-medium text-slate-800">{displayFor(key).title}</div>
                      {Object.entries(result.metrics)
                        .slice(0, 2)
                        .map(([label, value]) => (
                          <div key={label} className="flex justify-between gap-2 text-xs">
                            <span className="text-slate-500">{label}</span>
                            <span className="text-right font-medium text-slate-700">{value}</span>
                          </div>
                        ))}
                      {key === 'kmeans' && result.selection?.affected_percent != null && (
                        <div className="flex justify-between gap-2 text-xs">
                          <span className="text-slate-500">Approx. suspected area</span>
                          <span className="font-medium text-slate-700">{result.selection.affected_percent.toFixed(2)}% of leaf</span>
                        </div>
                      )}
                      <p className="pt-1 text-xs text-slate-500">{info.role}</p>
                    </div>
                  </>
                ) : (
                  <div className="flex flex-1 flex-col items-center justify-center gap-3 p-10 text-center">
                    <div className="text-sm font-medium text-slate-500">Not processed yet</div>
                    <p className="text-xs text-slate-400">{info.role}</p>
                    <Link to={`/process/${key}`} className="btn-secondary">
                      <Play size={14} /> Open {info.name}
                    </Link>
                  </div>
                )}
              </article>
            )
          })}
        </div>
      </div>
      <Lightbox image={open} onClose={() => setOpen(null)} />
    </div>
  )
}
