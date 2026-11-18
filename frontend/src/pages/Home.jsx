import { useNavigate } from 'react-router-dom'
import { ImageUp, Info, ShieldCheck } from 'lucide-react'
import Logo from '../components/Logo.jsx'
import AlgorithmCard from '../components/AlgorithmCard.jsx'
import { ALGORITHM_ORDER, ALGORITHMS } from '../content/algorithms.js'
import { useImage } from '../context/ImageContext.jsx'

export default function Home() {
  const navigate = useNavigate()
  const { image, results } = useImage()
  const select = (algorithm) => navigate(image ? `/process/${algorithm}` : `/upload?next=${algorithm}`)

  return (
    <div className="space-y-10">
      <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-leaf-900 via-leaf-800 to-leaf-700 px-6 py-10 text-white sm:px-10 sm:py-14">
        <div className="absolute -right-16 -top-16 h-64 w-64 rounded-full bg-white/5" />
        <div className="absolute -bottom-24 right-24 h-72 w-72 rounded-full bg-white/5" />
        <div className="relative max-w-3xl space-y-5">
          <div className="inline-flex items-center gap-3 rounded-2xl bg-white/10 px-3 py-2">
            <Logo size={30} withText={false} />
            <span className="text-lg font-bold tracking-tight">LeafGuard</span>
          </div>
          <h1 className="text-3xl font-bold leading-tight sm:text-4xl">
            Plant Leaf Disease-Affected Region Detection and Segmentation
          </h1>
          <p className="text-base text-leaf-100 sm:text-lg">
            A digital image-processing toolkit that applies four classical algorithms - K-Means clustering, HSV
            segmentation, histogram equalization and Canny edge detection - each implemented from scratch with
            NumPy, independently to the same uploaded leaf image.
          </p>
          <div className="flex flex-wrap gap-3">
            <button type="button" onClick={() => navigate('/upload')} className="inline-flex items-center gap-2 rounded-xl bg-white px-5 py-3 text-sm font-semibold text-leaf-900 shadow hover:bg-leaf-50">
              <ImageUp size={18} /> {image ? 'Replace image' : 'Upload Image'}
            </button>
            <button type="button" onClick={() => navigate('/learn')} className="inline-flex items-center gap-2 rounded-xl border border-white/40 px-5 py-3 text-sm font-semibold text-white hover:bg-white/10">
              How the algorithms work
            </button>
          </div>
        </div>
      </section>

      <section>
        <div className="mb-4 flex flex-wrap items-end justify-between gap-2">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">Four algorithms</h2>
            <p className="text-sm text-slate-500">Choose one at a time - each processes the original image independently.</p>
          </div>
        </div>
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {ALGORITHM_ORDER.map((key, index) => (
            <AlgorithmCard key={key} algorithm={key} index={index} processed={Boolean(results[key])} onSelect={select} />
          ))}
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <div className="card flex gap-3 p-5">
          <ShieldCheck className="shrink-0 text-leaf-800" />
          <div className="text-sm text-slate-600">
            <h3 className="mb-1 font-semibold text-slate-900">Implemented from scratch</h3>
            Every algorithm step - distances and centroids, RGB→HSV conversion, histogram and CDF, Gaussian and
            Sobel convolution, non-maximum suppression and hysteresis - is hand-written. Libraries are used only to
            read/write images, do array arithmetic and draw charts.
          </div>
        </div>
        <div className="card flex gap-3 p-5">
          <Info className="shrink-0 text-amber-600" />
          <div className="text-sm text-slate-600">
            <h3 className="mb-1 font-semibold text-slate-900">What the results mean</h3>
            {ALGORITHM_ORDER.map((k) => (
              <span key={k} className="block">
                <b>{ALGORITHMS[k].name}:</b> {ALGORITHMS[k].role}
              </span>
            ))}
            <span className="mt-1 block">These methods do not identify a specific disease.</span>
          </div>
        </div>
      </section>
    </div>
  )
}
