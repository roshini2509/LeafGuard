import { useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { FileImage, Loader2, RefreshCw, Trash2, UploadCloud } from 'lucide-react'
import { apiUrl, deleteImage, uploadImage } from '../api/client.js'
import { useImage } from '../context/ImageContext.jsx'
import { ErrorBanner, formatBytes } from '../components/common.jsx'
import AlgorithmCard from '../components/AlgorithmCard.jsx'
import { ALGORITHM_ORDER } from '../content/algorithms.js'

const ACCEPTED = ['image/jpeg', 'image/png', 'image/webp']
const MAX_BYTES = 15 * 1024 * 1024

export default function Upload() {
  const { image, results, setImage, clearImage } = useImage()
  const [dragging, setDragging] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const inputRef = useRef(null)
  const navigate = useNavigate()
  const [search] = useSearchParams()
  const next = search.get('next')

  async function handleFile(file) {
    if (!file) return
    setError('')
    const extensionOk = /\.(jpe?g|png|webp)$/i.test(file.name)
    if (!ACCEPTED.includes(file.type) && !extensionOk) {
      setError('Unsupported file type. Please choose a JPG, JPEG, PNG or WEBP image.')
      return
    }
    if (file.size > MAX_BYTES) {
      setError('The file is larger than 15 MB.')
      return
    }
    setBusy(true)
    try {
      const uploaded = await uploadImage(file)
      if (image) deleteImage(image.image_id).catch(() => {})   // tidy up the replaced upload
      setImage(uploaded)
      if (next) navigate(`/process/${next}`)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
      if (inputRef.current) inputRef.current.value = ''
    }
  }

  async function remove() {
    if (!image) return
    deleteImage(image.image_id).catch(() => {})
    clearImage()
  }

  const onDrop = (event) => {
    event.preventDefault()
    setDragging(false)
    handleFile(event.dataTransfer.files?.[0])
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Upload a leaf image</h1>
        <p className="text-sm text-slate-500">JPG, JPEG, PNG or WEBP, up to 15 MB. The original is stored unchanged and reused by every algorithm.</p>
      </div>

      <input
        ref={inputRef}
        type="file"
        accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp"
        className="hidden"
        onChange={(e) => handleFile(e.target.files?.[0])}
        data-testid="file-input"
      />

      {!image ? (
        <div
          onDragOver={(e) => {
            e.preventDefault()
            setDragging(true)
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && inputRef.current?.click()}
          className={`flex cursor-pointer flex-col items-center justify-center gap-3 rounded-3xl border-2 border-dashed p-12 text-center transition ${
            dragging ? 'border-leaf-700 bg-leaf-50' : 'border-slate-300 bg-white hover:border-leaf-700 hover:bg-leaf-50/50'
          }`}
        >
          {busy ? <Loader2 className="animate-spin text-leaf-800" size={40} /> : <UploadCloud className="text-leaf-800" size={44} />}
          <div className="text-lg font-semibold text-slate-900">{busy ? 'Uploading…' : 'Drag and drop your leaf image here'}</div>
          <div className="text-sm text-slate-500">or</div>
          <span className="btn-primary">
            <FileImage size={16} /> Browse files
          </span>
        </div>
      ) : (
        <div className="card grid gap-6 p-5 md:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)]">
          <div className="checkerboard overflow-hidden rounded-2xl">
            <img src={apiUrl(image.original_url)} alt="Uploaded leaf" className="mx-auto max-h-96 object-contain" />
          </div>
          <div className="flex flex-col gap-4">
            <dl className="grid grid-cols-2 gap-3 text-sm">
              {[
                ['Filename', image.filename],
                ['Dimensions', `${image.width} × ${image.height} px`],
                ['File size', formatBytes(image.size_bytes)],
                ['Algorithms run', `${Object.keys(results).length} of 4`],
              ].map(([label, value]) => (
                <div key={label} className="rounded-xl bg-slate-50 p-3">
                  <dt className="text-xs text-slate-500">{label}</dt>
                  <dd className="break-all font-medium text-slate-900">{value}</dd>
                </div>
              ))}
            </dl>
            <div className="flex flex-wrap gap-2">
              <button type="button" className="btn-secondary" onClick={() => inputRef.current?.click()} disabled={busy}>
                {busy ? <Loader2 size={16} className="animate-spin" /> : <RefreshCw size={16} />} Replace image
              </button>
              <button type="button" className="btn-secondary hover:!border-red-400 hover:!text-red-700" onClick={remove}>
                <Trash2 size={16} /> Remove image
              </button>
            </div>
            <div className="rounded-xl bg-leaf-50 p-4 text-leaf-900">
              <div className="font-semibold">Choose an algorithm to process your leaf image.</div>
              <div className="text-sm">Nothing runs automatically - pick one below and press Run.</div>
            </div>
          </div>
        </div>
      )}

      <ErrorBanner message={error} onClose={() => setError('')} />

      {image && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {ALGORITHM_ORDER.map((key, index) => (
            <AlgorithmCard
              key={key}
              algorithm={key}
              index={index}
              compact
              processed={Boolean(results[key])}
              onSelect={(a) => navigate(`/process/${a}`)}
            />
          ))}
        </div>
      )}
    </div>
  )
}
