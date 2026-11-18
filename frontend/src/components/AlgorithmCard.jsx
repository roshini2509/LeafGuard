import { ArrowRight, CheckCircle2 } from 'lucide-react'
import { ALGORITHMS } from '../content/algorithms.js'
import { ILLUSTRATIONS } from './Illustrations.jsx'

export default function AlgorithmCard({ algorithm, index, processed, onSelect, compact = false }) {
  const info = ALGORITHMS[algorithm]
  const Illustration = ILLUSTRATIONS[algorithm]
  return (
    <article className="card group flex flex-col overflow-hidden transition hover:-translate-y-0.5 hover:shadow-md">
      {!compact && (
        <div className="relative h-36 bg-leaf-50 p-3">
          <Illustration />
          <span className="absolute bottom-2 right-2 rounded-md bg-white/80 px-1.5 py-0.5 text-[10px] text-slate-500">
            illustration
          </span>
        </div>
      )}
      <div className="flex flex-1 flex-col gap-2 p-5">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wide text-leaf-700">Algorithm {index + 1}</span>
          {processed && (
            <span className="chip">
              <CheckCircle2 size={12} /> processed
            </span>
          )}
        </div>
        <h3 className="text-lg font-semibold text-slate-900">{info.name}</h3>
        <p className="flex-1 text-sm text-slate-600">{info.short}</p>
        <button type="button" className="btn-primary mt-2 w-full" onClick={() => onSelect(algorithm)}>
          Select Algorithm <ArrowRight size={16} />
        </button>
      </div>
    </article>
  )
}
