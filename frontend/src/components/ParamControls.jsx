// Algorithm-specific parameter controls. Each control edits `params` via onChange.

const HSV_PRESETS = {
  green: { label: 'Healthy green', h_min: 70, h_max: 170, s_min: 25, s_max: 100, v_min: 15, v_max: 100 },
  yellow: { label: 'Yellow', h_min: 40, h_max: 70, s_min: 30, s_max: 100, v_min: 40, v_max: 100 },
  brown: { label: 'Brown', h_min: 10, h_max: 40, s_min: 25, s_max: 100, v_min: 10, v_max: 70 },
  dark: { label: 'Dark lesion', h_min: 0, h_max: 360, s_min: 0, s_max: 100, v_min: 0, v_max: 25 },
  red: { label: 'Red / rust', h_min: 340, h_max: 15, s_min: 35, s_max: 100, v_min: 20, v_max: 100 },
}

function Field({ label, hint, children }) {
  return (
    <label className="block">
      <span className="flex items-baseline justify-between text-sm font-medium text-slate-700">{label}</span>
      {children}
      {hint && <span className="mt-1 block text-xs text-slate-500">{hint}</span>}
    </label>
  )
}

function Slider({ label, value, min, max, step = 1, onChange, unit = '', hint, format }) {
  return (
    <Field
      label={
        <>
          <span>{label}</span>
          <span className="font-mono text-xs text-leaf-800">
            {format ? format(value) : value}
            {unit}
          </span>
        </>
      }
      hint={hint}
    >
      <input
        type="range"
        className="mt-1 w-full"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
      />
    </Field>
  )
}

function Segmented({ label, options, value, onChange }) {
  return (
    <Field label={label}>
      <div className="mt-1 grid grid-flow-col gap-1 rounded-xl bg-slate-100 p-1">
        {options.map((option) => (
          <button
            key={option.value}
            type="button"
            onClick={() => onChange(option.value)}
            className={`rounded-lg px-2 py-1.5 text-xs font-medium transition ${
              value === option.value ? 'bg-white text-leaf-900 shadow' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            {option.label}
          </button>
        ))}
      </div>
    </Field>
  )
}

function KMeansControls({ params, set }) {
  return (
    <>
      <Slider label="Number of clusters K" value={params.k} min={2} max={8} onChange={(v) => set({ k: v })} />
      <Slider label="Maximum iterations" value={params.max_iterations} min={5} max={300} step={5} onChange={(v) => set({ max_iterations: v })} />
      <Field label="Convergence tolerance">
        <select
          className="mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm"
          value={params.tolerance}
          onChange={(e) => set({ tolerance: Number(e.target.value) })}
        >
          {[0.01, 0.001, 0.0001, 0.00001, 0.000001].map((t) => (
            <option key={t} value={t}>
              {t.toExponential(0)}
            </option>
          ))}
        </select>
      </Field>
      <Segmented
        label="Initialisation"
        value={params.init_method}
        onChange={(v) => set({ init_method: v })}
        options={[{ value: 'k-means++', label: 'K-Means++' }, { value: 'random', label: 'Random' }]}
      />
      <Segmented
        label="Colour space"
        value={params.colour_space}
        onChange={(v) => set({ colour_space: v })}
        options={[{ value: 'Lab', label: 'Lab (manual)' }, { value: 'RGB', label: 'RGB' }]}
      />
      <Field label="Random seed">
        <input
          type="number"
          min={0}
          className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
          value={params.seed}
          onChange={(e) => set({ seed: Math.max(0, Math.floor(Number(e.target.value) || 0)) })}
        />
      </Field>
    </>
  )
}

function HueBar({ hMin, hMax }) {
  const wraps = hMin > hMax
  const left = (v) => `${(v / 360) * 100}%`
  return (
    <div className="relative mt-1 h-3 rounded-full" style={{ background: 'linear-gradient(90deg, hsl(0 80% 50%), hsl(60 80% 50%), hsl(120 80% 40%), hsl(180 80% 45%), hsl(240 80% 55%), hsl(300 80% 50%), hsl(360 80% 50%))' }}>
      {wraps ? (
        <>
          <div className="absolute inset-y-0 rounded-full border-2 border-slate-900" style={{ left: left(hMin), right: 0 }} />
          <div className="absolute inset-y-0 rounded-full border-2 border-slate-900" style={{ left: 0, width: left(hMax) }} />
        </>
      ) : (
        <div className="absolute inset-y-0 rounded-full border-2 border-slate-900" style={{ left: left(hMin), width: `${((hMax - hMin) / 360) * 100}%` }} />
      )}
    </div>
  )
}

function HSVControls({ params, set }) {
  return (
    <>
      <Field label="Colour presets" hint="Starting points only - adjust the ranges to match your image.">
        <div className="mt-1 flex flex-wrap gap-1.5">
          {Object.entries(HSV_PRESETS).map(([key, preset]) => (
            <button
              key={key}
              type="button"
              className="rounded-full border border-slate-300 px-3 py-1 text-xs font-medium hover:border-leaf-700 hover:bg-leaf-50"
              onClick={() => {
                const { label: _label, ...values } = preset
                set(values)
              }}
            >
              {preset.label}
            </button>
          ))}
        </div>
      </Field>
      <div>
        <Slider label="Minimum hue" value={params.h_min} min={0} max={360} unit="°" onChange={(v) => set({ h_min: v })} />
        <Slider label="Maximum hue" value={params.h_max} min={0} max={360} unit="°" onChange={(v) => set({ h_max: v })} />
        <HueBar hMin={params.h_min} hMax={params.h_max} />
        {params.h_min > params.h_max && (
          <p className="mt-1 text-xs text-amber-700">Min &gt; max: the hue range wraps around 0° (e.g. reds).</p>
        )}
      </div>
      <Slider label="Minimum saturation" value={params.s_min} min={0} max={100} unit="%" onChange={(v) => set({ s_min: Math.min(v, params.s_max) })} />
      <Slider label="Maximum saturation" value={params.s_max} min={0} max={100} unit="%" onChange={(v) => set({ s_max: Math.max(v, params.s_min) })} />
      <Slider label="Minimum value" value={params.v_min} min={0} max={100} unit="%" onChange={(v) => set({ v_min: Math.min(v, params.v_max) })} />
      <Slider label="Maximum value" value={params.v_max} min={0} max={100} unit="%" onChange={(v) => set({ v_max: Math.max(v, params.v_min) })} />
    </>
  )
}

function HistogramControls() {
  return (
    <p className="rounded-xl bg-leaf-50 p-3 text-sm text-leaf-900">
      Histogram equalization has no tunable parameters: the transformation is computed entirely from the image’s
      own cumulative distribution.
    </p>
  )
}

function CannyControls({ params, set }) {
  const ratio = params.threshold_mode === 'Ratio of max'
  return (
    <>
      <Field label="Gaussian kernel size">
        <div className="mt-1 grid grid-cols-6 gap-1">
          {[3, 5, 7, 9, 11, 13].map((size) => (
            <button
              key={size}
              type="button"
              onClick={() => set({ kernel_size: size })}
              className={`rounded-lg border py-1.5 text-xs font-medium ${
                params.kernel_size === size ? 'border-leaf-800 bg-leaf-800 text-white' : 'border-slate-300 hover:border-leaf-700'
              }`}
            >
              {size}
            </button>
          ))}
        </div>
      </Field>
      <Slider label="Gaussian sigma σ" value={params.sigma} min={0.5} max={5} step={0.1} onChange={(v) => set({ sigma: v })} format={(v) => v.toFixed(1)} />
      <Segmented
        label="Threshold mode"
        value={params.threshold_mode}
        onChange={(v) =>
          set(v === 'Ratio of max' ? { threshold_mode: v, low: 0.05, high: 0.15 } : { threshold_mode: v, low: 0.1, high: 0.3 })
        }
        options={[{ value: 'Ratio of max', label: 'Ratio of max' }, { value: 'Absolute', label: 'Absolute' }]}
      />
      <Slider
        label="Lower threshold"
        value={params.low}
        min={0}
        max={ratio ? 0.9 : 3}
        step={0.01}
        format={(v) => v.toFixed(2)}
        onChange={(v) => set({ low: Math.min(v, params.high) })}
        hint={ratio ? 'Fraction of the strongest NMS response.' : 'Absolute gradient magnitude (image scaled 0-1).'}
      />
      <Slider
        label="Upper threshold"
        value={params.high}
        min={0.01}
        max={ratio ? 1 : 4}
        step={0.01}
        format={(v) => v.toFixed(2)}
        onChange={(v) => set({ high: Math.max(v, params.low) })}
      />
    </>
  )
}

const CONTROLS = { kmeans: KMeansControls, hsv: HSVControls, histogram: HistogramControls, canny: CannyControls }

export default function ParamControls({ algorithm, params, onChange, maxSide, onMaxSide }) {
  const Controls = CONTROLS[algorithm]
  const set = (patch) => onChange({ ...params, ...patch })
  return (
    <div className="space-y-4">
      <Controls params={params} set={set} />
      <details className="rounded-xl border border-slate-200 p-3">
        <summary className="cursor-pointer text-sm font-medium text-slate-700">Advanced: processing size</summary>
        <div className="mt-3">
          <Slider
            label="Longest side of the processing copy"
            value={maxSide}
            min={128}
            max={800}
            step={16}
            unit=" px"
            onChange={onMaxSide}
            hint="The original upload is never modified; a resized copy is processed so the hand-written loops stay fast."
          />
        </div>
      </details>
    </div>
  )
}
