import { useState } from 'react'
import { Link, NavLink, Navigate, useParams } from 'react-router-dom'
import { Play } from 'lucide-react'
import { ALGORITHM_ORDER, ALGORITHMS } from '../content/algorithms.js'
import { useImage } from '../context/ImageContext.jsx'
import Explanation from '../components/Explanation.jsx'
import { ImageCard, Lightbox, SectionTitle } from '../components/common.jsx'

const MANUAL_VS_LIBRARY = [
  ['Reading / writing JPG, PNG, WEBP; basic resize', 'Pillow (permitted image handling)'],
  ['Array creation, element-wise arithmetic, reshaping, indexing', 'NumPy'],
  ['Drawing histograms, CDF curves and comparison figures', 'Matplotlib (drawing only - counts are computed by hand)'],
  ['HTTP API and user interface', 'FastAPI, React, Tailwind CSS'],
  ['Grayscale conversion, RGB → HSV, RGB → Lab', 'Manual (utils/image_converter.py, algorithms/hsv_segmentation.py)'],
  ['K-Means: initialisation, distances, assignment, centroid update, convergence', 'Manual (algorithms/kmeans.py)'],
  ['HSV thresholds incl. hue wrap-around', 'Manual (algorithms/hsv_segmentation.py)'],
  ['Histogram counting, CDF, transformation table, mapping', 'Manual (algorithms/histogram_equalization.py)'],
  ['Gaussian & Sobel kernels, padding, convolution, NMS, double threshold, hysteresis', 'Manual (utils/convolution.py, algorithms/canny.py)'],
  ['cv2.kmeans, cv2.inRange, cv2.cvtColor, cv2.equalizeHist, cv2.Canny, scikit-image, SciPy', 'NOT used (a test scans the source code)'],
]

export default function Learn() {
  const { algorithm } = useParams()
  const { results } = useImage()
  const [open, setOpen] = useState(null)
  if (!ALGORITHM_ORDER.includes(algorithm)) return <Navigate to="/learn/kmeans" replace />
  const info = ALGORITHMS[algorithm]
  const result = results[algorithm]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">How the algorithms work</h1>
        <p className="text-sm text-slate-500">Presentation notes: definitions, formulas, step-by-step working and limitations.</p>
      </div>
      <div className="flex flex-wrap gap-2">
        {ALGORITHM_ORDER.map((key) => (
          <NavLink
            key={key}
            to={`/learn/${key}`}
            className={({ isActive }) =>
              `rounded-xl px-3 py-2 text-sm font-medium ${isActive ? 'bg-leaf-800 text-white' : 'bg-white text-slate-600 ring-1 ring-slate-200 hover:ring-leaf-700'}`
            }
          >
            {ALGORITHMS[key].name}
          </NavLink>
        ))}
      </div>

      <section className="card space-y-6 p-6">
        <h2 className="text-xl font-semibold text-slate-900">{info.name}</h2>
        <Explanation algorithm={algorithm} full />
      </section>

      <section className="card p-6">
        <SectionTitle icon={Play}>Intermediate stages and actual output on your image</SectionTitle>
        {result ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {result.stages.slice(0, 8).map((stage) => (
              <ImageCard key={stage.url} image={stage} onOpen={setOpen} />
            ))}
          </div>
        ) : (
          <p className="text-sm text-slate-600">
            You have not run {info.name} yet.{' '}
            <Link className="font-medium text-leaf-800 underline" to={`/process/${algorithm}`}>
              Run it on your image
            </Link>{' '}
            to see its real intermediate stages and output here.
          </p>
        )}
      </section>

      <section className="card p-6">
        <SectionTitle>Built-in functions vs. manual implementation</SectionTitle>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="py-2 pr-4">Operation</th>
                <th className="py-2">Done by</th>
              </tr>
            </thead>
            <tbody>
              {MANUAL_VS_LIBRARY.map(([operation, by]) => (
                <tr key={operation} className="border-b border-slate-100">
                  <td className="py-2 pr-4">{operation}</td>
                  <td className={`py-2 ${by.startsWith('Manual') ? 'font-medium text-leaf-800' : by.startsWith('NOT') ? 'font-medium text-red-700' : 'text-slate-600'}`}>
                    {by}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <Lightbox image={open} onClose={() => setOpen(null)} />
    </div>
  )
}
