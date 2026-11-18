import { useState } from 'react'
import { BarChart3, BookOpen, Clock, Download, FileArchive, Images, Layers, Ruler, Settings2, SlidersHorizontal } from 'lucide-react'
import { apiUrl } from '../api/client.js'
import { BeforeAfter, ImageCard, Lightbox, SectionTitle } from './common.jsx'
import ClusterPanel from './ClusterPanel.jsx'
import Explanation from './Explanation.jsx'

const PARAM_LABELS = {
  max_side: 'Processing size (px)',
  k: 'K',
  max_iterations: 'Max iterations',
  tolerance: 'Tolerance',
  init_method: 'Initialisation',
  colour_space: 'Colour space',
  seed: 'Seed',
  h_min: 'Hue min (°)',
  h_max: 'Hue max (°)',
  s_min: 'Saturation min (%)',
  s_max: 'Saturation max (%)',
  v_min: 'Value min (%)',
  v_max: 'Value max (%)',
  kernel_size: 'Gaussian kernel size',
  sigma: 'Gaussian sigma',
  low: 'Lower threshold',
  high: 'Upper threshold',
  threshold_mode: 'Threshold mode',
}

export default function ResultView({ result }) {
  const [open, setOpen] = useState(null)
  const finalImage = result.final
  const otherStages = result.stages.filter((s) => s.url !== result.original.url)

  return (
    <div className="space-y-8">
      {/* header */}
      <div className="card flex flex-wrap items-center gap-x-6 gap-y-2 p-4">
        <div>
          <div className="text-xs uppercase tracking-wide text-slate-500">Result</div>
          <div className="text-lg font-semibold text-slate-900">{result.algorithm_name}</div>
        </div>
        <span className="flex items-center gap-1.5 text-sm text-slate-600">
          <Clock size={16} className="text-leaf-800" /> {(result.time_seconds * 1000).toFixed(0)} ms processing
        </span>
        <span className="flex items-center gap-1.5 text-sm text-slate-600">
          <Ruler size={16} className="text-leaf-800" /> {result.input_size.width} × {result.input_size.height} px
        </span>
        <div className="ml-auto flex flex-wrap gap-2">
          <a className="btn-secondary" href={apiUrl(finalImage.url)} download={finalImage.filename}>
            <Download size={16} /> Processed image
          </a>
          <a className="btn-primary" href={apiUrl(result.zip_url)}>
            <FileArchive size={16} /> All outputs (ZIP)
          </a>
        </div>
      </div>

      {/* before / after */}
      <section>
        <SectionTitle icon={Images}>Original vs processed</SectionTitle>
        <div className="grid gap-4 lg:grid-cols-3">
          <ImageCard image={result.original} onOpen={setOpen} />
          <ImageCard image={finalImage} onOpen={setOpen} badge="output" />
          <BeforeAfter before={result.original.url} after={finalImage.url} afterLabel={finalImage.title.split('(')[0]} />
        </div>
      </section>

      {/* metrics + interpretation */}
      <section className="grid gap-4 lg:grid-cols-3">
        <div className="card p-4 lg:col-span-1">
          <SectionTitle icon={BarChart3}>Measurements</SectionTitle>
          <dl className="space-y-2 text-sm">
            {Object.entries(result.metrics).map(([label, value]) => (
              <div key={label} className="flex justify-between gap-4 border-b border-slate-100 pb-1.5">
                <dt className="text-slate-500">{label}</dt>
                <dd className="text-right font-medium text-slate-900">{value}</dd>
              </div>
            ))}
          </dl>
        </div>
        <div className="card p-4 lg:col-span-2">
          <SectionTitle icon={BookOpen}>Interpretation</SectionTitle>
          <p className="text-sm leading-relaxed text-slate-700">{result.interpretation}</p>
        </div>
      </section>

      {result.algorithm === 'kmeans' && (
        <section className="card p-5">
          <SectionTitle icon={Layers}>Inspect clusters and select a suspected region</SectionTitle>
          <ClusterPanel key={result.run_id} result={result} onOpen={setOpen} />
        </section>
      )}

      {/* charts (Matplotlib) */}
      <section>
        <SectionTitle icon={BarChart3}>Charts and comparisons (Matplotlib)</SectionTitle>
        <div className="grid gap-4 md:grid-cols-2">
          {result.charts.map((chart) => (
            <ImageCard key={chart.url} image={chart} onOpen={setOpen} tall />
          ))}
        </div>
      </section>

      {/* intermediate stages */}
      <section>
        <SectionTitle icon={SlidersHorizontal}>Intermediate processing stages</SectionTitle>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {otherStages.map((stage, i) => (
            <ImageCard key={stage.url} image={stage} onOpen={setOpen} badge={`${i + 2}`} />
          ))}
        </div>
      </section>

      {/* parameters */}
      <section className="grid gap-4 lg:grid-cols-3">
        <div className="card p-4">
          <SectionTitle icon={Settings2}>Parameters used</SectionTitle>
          <table className="w-full text-sm">
            <tbody>
              {Object.entries(result.params).map(([key, value]) => (
                <tr key={key} className="border-b border-slate-100">
                  <td className="py-1.5 pr-3 text-slate-500">{PARAM_LABELS[key] ?? key}</td>
                  <td className="py-1.5 text-right font-mono text-slate-900">{String(value)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="card p-4 lg:col-span-2">
          <SectionTitle icon={BookOpen}>Mathematical explanation</SectionTitle>
          <Explanation algorithm={result.algorithm} />
        </div>
      </section>

      <Lightbox image={open} onClose={() => setOpen(null)} />
    </div>
  )
}
