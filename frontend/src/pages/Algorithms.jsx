import { Link, useNavigate } from 'react-router-dom'
import { ImageUp } from 'lucide-react'
import AlgorithmCard from '../components/AlgorithmCard.jsx'
import { ALGORITHM_ORDER } from '../content/algorithms.js'
import { useImage } from '../context/ImageContext.jsx'
import { apiUrl } from '../api/client.js'

export default function Algorithms() {
  const { image, results } = useImage()
  const navigate = useNavigate()
  const select = (algorithm) => navigate(image ? `/process/${algorithm}` : `/upload?next=${algorithm}`)

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Select an algorithm</h1>
          <p className="text-sm text-slate-500">
            Each algorithm processes the <b>original</b> uploaded image on its own - outputs are never chained.
          </p>
        </div>
        {image ? (
          <div className="card flex items-center gap-3 p-2 pr-4">
            <img src={apiUrl(image.original_url)} alt="" className="h-12 w-12 rounded-lg object-cover" />
            <div className="text-sm">
              <div className="font-medium text-slate-900">{image.filename}</div>
              <div className="text-xs text-slate-500">
                {image.width} × {image.height} px
              </div>
            </div>
          </div>
        ) : (
          <Link to="/upload" className="btn-primary">
            <ImageUp size={16} /> Upload an image first
          </Link>
        )}
      </div>
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {ALGORITHM_ORDER.map((key, index) => (
          <AlgorithmCard key={key} algorithm={key} index={index} processed={Boolean(results[key])} onSelect={select} />
        ))}
      </div>
    </div>
  )
}
