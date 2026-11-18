import { ALGORITHMS } from '../content/algorithms.js'
import { MathBlock } from './common.jsx'

/** Definition, formulas, steps, parameters and (optionally) pros/cons/applications. */
export default function Explanation({ algorithm, full = false }) {
  const info = ALGORITHMS[algorithm]
  return (
    <div className="space-y-5 text-sm leading-relaxed text-slate-700">
      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <h3 className="mb-1 font-semibold text-slate-900">Definition</h3>
          <p>{info.definition}</p>
        </div>
        <div>
          <h3 className="mb-1 font-semibold text-slate-900">Purpose in this project</h3>
          <p>{info.purpose}</p>
        </div>
      </div>
      <div>
        <h3 className="mb-2 font-semibold text-slate-900">Mathematical formulas</h3>
        <div className="grid gap-2 lg:grid-cols-2">
          {info.formulas.map((f) => (
            <MathBlock key={f.label} label={f.label} tex={f.tex} />
          ))}
        </div>
      </div>
      <div>
        <h3 className="mb-2 font-semibold text-slate-900">Step-by-step working</h3>
        <ol className="space-y-1.5">
          {info.steps.map((step, i) => (
            <li key={i} className="flex gap-3">
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-leaf-100 text-xs font-semibold text-leaf-900">
                {i + 1}
              </span>
              <span>{step}</span>
            </li>
          ))}
        </ol>
      </div>
      <div>
        <h3 className="mb-2 font-semibold text-slate-900">Parameters</h3>
        <dl className="grid gap-x-6 gap-y-2 md:grid-cols-2">
          {info.params.map(([name, text]) => (
            <div key={name}>
              <dt className="font-medium text-slate-900">{name}</dt>
              <dd className="text-slate-600">{text}</dd>
            </div>
          ))}
        </dl>
      </div>
      {full && (
        <>
          <div>
            <h3 className="mb-1 font-semibold text-slate-900">Intermediate stages</h3>
            <p>{info.stagesInfo}</p>
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            {[
              ['Advantages', info.advantages, 'bg-leaf-50 text-leaf-900'],
              ['Limitations', info.limitations, 'bg-amber-50 text-amber-900'],
              ['Real-world applications', info.applications, 'bg-sky-50 text-sky-900'],
            ].map(([title, items, colours]) => (
              <div key={title} className={`rounded-xl p-4 ${colours}`}>
                <h3 className="mb-2 font-semibold">{title}</h3>
                <ul className="list-disc space-y-1 pl-4">
                  {items.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
