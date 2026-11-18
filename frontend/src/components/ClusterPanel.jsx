import { useState } from 'react'
import { Loader2, Wand2 } from 'lucide-react'
import { selectClusters } from '../api/client.js'
import { useImage } from '../context/ImageContext.jsx'
import { ErrorBanner, ImageCard } from './common.jsx'

/** Let the user inspect the K-Means clusters and choose background / suspected clusters. */
export default function ClusterPanel({ result, onOpen }) {
  const { updateResult } = useImage()
  const clusters = result.extra.clusters
  const asList = (value, fallback) => (Array.isArray(value) ? value : fallback)
  const [background, setBackground] = useState(() =>
    asList(result.selection?.background_clusters, result.extra.suggested_background),
  )
  const [suspected, setSuspected] = useState(() =>
    asList(result.selection?.suspected_clusters, result.extra.suggested_suspected),
  )
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const selection = result.selection

  const toggle = (list, setList, cluster) =>
    setList(list.includes(cluster) ? list.filter((c) => c !== cluster) : [...list, cluster].sort())

  async function apply() {
    setBusy(true)
    setError('')
    try {
      const response = await selectClusters(result.image_id, result.run_id, background, suspected)
      updateResult('kmeans', { selection: response })
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-600">
        Clusters are numbered from darkest to brightest. They are <b>colour groups, not disease labels</b> - the
        darkest or brownest cluster is not automatically diseased. The pre-ticked boxes are only a heuristic
        suggestion (background = clusters covering much of the image border; suspected = clearly non-green
        clusters). Change them to match what you see.
      </p>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-500">
              <th className="py-2 pr-3">Cluster</th>
              <th className="py-2 pr-3">Mean colour</th>
              <th className="py-2 pr-3">Pixels</th>
              <th className="py-2 pr-3">Excess green</th>
              <th className="py-2 pr-3">Border share</th>
              <th className="py-2 pr-3 text-center">Background</th>
              <th className="py-2 pr-3 text-center">Suspected</th>
            </tr>
          </thead>
          <tbody>
            {clusters.map((c) => (
              <tr key={c.cluster} className="border-b border-slate-100">
                <td className="py-2 pr-3 font-medium">C{c.cluster + 1}</td>
                <td className="py-2 pr-3">
                  <span className="inline-flex items-center gap-2">
                    <span
                      className="h-5 w-5 rounded-md border border-slate-300"
                      style={{ background: `rgb(${c.mean_rgb.join(',')})` }}
                    />
                    <span className="font-mono text-xs text-slate-500">({c.mean_rgb.join(', ')})</span>
                  </span>
                </td>
                <td className="py-2 pr-3">{c.percent.toFixed(1)}%</td>
                <td className="py-2 pr-3">{c.excess_green.toFixed(2)}</td>
                <td className="py-2 pr-3">{(100 * c.border_share).toFixed(0)}%</td>
                <td className="py-2 pr-3 text-center">
                  <input type="checkbox" className="h-4 w-4 accent-blue-600" checked={background.includes(c.cluster)} onChange={() => toggle(background, setBackground, c.cluster)} aria-label={`C${c.cluster + 1} is background`} />
                </td>
                <td className="py-2 pr-3 text-center">
                  <input type="checkbox" className="h-4 w-4 accent-red-600" checked={suspected.includes(c.cluster)} onChange={() => toggle(suspected, setSuspected, c.cluster)} aria-label={`C${c.cluster + 1} is suspected`} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <button type="button" className="btn-primary" onClick={apply} disabled={busy}>
        {busy ? <Loader2 size={16} className="animate-spin" /> : <Wand2 size={16} />} Build suspected-region mask
      </button>
      <ErrorBanner message={error} onClose={() => setError('')} />
      {selection && (
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-3 rounded-xl bg-amber-50 p-3 text-sm text-amber-900">
            <b>Approximate visual segmentation</b>
            {selection.affected_percent != null ? (
              <span>
                Suspected clusters cover <b>{selection.affected_percent.toFixed(2)}%</b> of the non-background (leaf)
                pixels.
              </span>
            ) : (
              <span>Mark at least one background cluster to estimate the percentage of the leaf area.</span>
            )}
            <span className="text-xs">Not a diagnosis.</span>
          </div>
          <div className="grid gap-4 sm:grid-cols-3">
            <ImageCard image={selection.background_image} onOpen={onOpen} />
            <ImageCard image={selection.mask} onOpen={onOpen} />
            <ImageCard image={selection.overlay} onOpen={onOpen} badge="approximate" />
          </div>
        </div>
      )}
    </div>
  )
}
