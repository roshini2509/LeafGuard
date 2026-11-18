import { useEffect, useState } from 'react'
import katex from 'katex'
import { AlertTriangle, Download, Loader2, Maximize2, X } from 'lucide-react'
import { apiUrl } from '../api/client.js'

/** Render a LaTeX formula with KaTeX. */
export function MathBlock({ tex, label }) {
  const html = katex.renderToString(tex, { displayMode: true, throwOnError: false })
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-2">
      {label && <div className="text-xs font-medium text-slate-500">{label}</div>}
      <div className="overflow-x-auto" dangerouslySetInnerHTML={{ __html: html }} />
    </div>
  )
}

export function ErrorBanner({ message, onClose }) {
  if (!message) return null
  return (
    <div role="alert" className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
      <AlertTriangle size={18} className="mt-0.5 shrink-0" />
      <div className="flex-1">
        <div className="font-semibold">Something went wrong</div>
        <div>{message}</div>
      </div>
      {onClose && (
        <button type="button" onClick={onClose} className="text-red-500 hover:text-red-700" aria-label="Dismiss">
          <X size={16} />
        </button>
      )}
    </div>
  )
}

export function LoadingOverlay({ text = 'Processing…' }) {
  return (
    <div className="absolute inset-0 z-20 flex flex-col items-center justify-center gap-3 rounded-2xl bg-white/80 backdrop-blur-sm">
      <Loader2 className="animate-spin text-leaf-800" size={36} />
      <div className="text-sm font-medium text-leaf-900">{text}</div>
    </div>
  )
}

/** Click-to-enlarge viewer. */
export function Lightbox({ image, onClose }) {
  useEffect(() => {
    const onKey = (event) => event.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])
  if (!image) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/80 p-4" onClick={onClose}>
      <figure className="max-h-full max-w-5xl" onClick={(e) => e.stopPropagation()}>
        <img src={apiUrl(image.url)} alt={image.title} className="max-h-[80vh] rounded-xl bg-white object-contain" style={{ imageRendering: 'pixelated' }} />
        <figcaption className="mt-3 flex items-center justify-between gap-4 text-sm text-white">
          <span>
            <b>{image.title}</b> {image.caption && <span className="opacity-80">- {image.caption}</span>}
          </span>
          <span className="flex gap-2">
            <a className="btn-secondary !py-1.5" href={apiUrl(image.url)} download={image.filename}>
              <Download size={14} /> Download
            </a>
            <button type="button" className="btn-secondary !py-1.5" onClick={onClose}>
              <X size={14} /> Close
            </button>
          </span>
        </figcaption>
      </figure>
    </div>
  )
}

/** A rounded image card with title, caption, enlarge and download buttons. */
export function ImageCard({ image, onOpen, tall = false, badge }) {
  if (!image) return null
  return (
    <figure className="card overflow-hidden">
      <button type="button" className="checkerboard group relative block w-full" onClick={() => onOpen?.(image)}>
        <img
          src={apiUrl(image.url)}
          alt={image.title}
          loading="lazy"
          className={`mx-auto w-full object-contain ${tall ? 'max-h-[28rem]' : 'aspect-square'}`}
        />
        <span className="absolute right-2 top-2 rounded-lg bg-white/90 p-1.5 text-slate-600 opacity-0 shadow transition group-hover:opacity-100">
          <Maximize2 size={14} />
        </span>
        {badge && <span className="chip absolute left-2 top-2 shadow">{badge}</span>}
      </button>
      <figcaption className="flex items-start justify-between gap-2 p-3">
        <div className="min-w-0">
          <div className="text-sm font-medium text-slate-800">{image.title}</div>
          {image.caption && <div className="text-xs text-slate-500">{image.caption}</div>}
        </div>
        <a
          href={apiUrl(image.url)}
          download={image.filename}
          className="shrink-0 rounded-lg p-1.5 text-slate-500 hover:bg-leaf-50 hover:text-leaf-800"
          title="Download PNG"
        >
          <Download size={16} />
        </a>
      </figcaption>
    </figure>
  )
}

/** Drag the divider to compare the original (left) and the processed image (right). */
export function BeforeAfter({ before, after, beforeLabel = 'Original', afterLabel = 'Processed' }) {
  const [position, setPosition] = useState(50)
  return (
    <div className="card overflow-hidden">
      <div className="checkerboard relative select-none">
        <img src={apiUrl(after)} alt={afterLabel} className="block w-full" draggable={false} />
        <div className="absolute inset-0 overflow-hidden" style={{ clipPath: `inset(0 ${100 - position}% 0 0)` }}>
          <img src={apiUrl(before)} alt={beforeLabel} className="block w-full" draggable={false} />
        </div>
        <div className="pointer-events-none absolute inset-y-0 w-0.5 bg-white shadow" style={{ left: `${position}%` }} />
        <span className="chip absolute left-2 top-2 shadow">{beforeLabel}</span>
        <span className="chip absolute right-2 top-2 shadow">{afterLabel}</span>
        <input
          type="range"
          min="0"
          max="100"
          value={position}
          onChange={(e) => setPosition(Number(e.target.value))}
          className="absolute inset-0 h-full w-full cursor-ew-resize opacity-0"
          aria-label="Before/after slider"
        />
      </div>
      <div className="px-3 py-2 text-xs text-slate-500">Drag across the image to compare before and after.</div>
    </div>
  )
}

export function SectionTitle({ icon: Icon, children, right }) {
  return (
    <div className="mb-3 flex items-center justify-between gap-3">
      <h2 className="flex items-center gap-2 text-lg font-semibold text-slate-900">
        {Icon && <Icon size={18} className="text-leaf-800" />} {children}
      </h2>
      {right}
    </div>
  )
}

export function formatBytes(bytes) {
  if (bytes == null) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`
}
