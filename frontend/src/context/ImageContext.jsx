import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'

/**
 * Holds the uploaded image (metadata only - the original file stays on the backend)
 * and the latest result of each algorithm. Saved in sessionStorage so a page refresh
 * keeps the session. Results are only ever added by running an algorithm.
 */
const ImageContext = createContext(null)
const STORAGE_KEY = 'leafguard-session-v1'

function loadSession() {
  try {
    const saved = JSON.parse(sessionStorage.getItem(STORAGE_KEY) || 'null')
    if (saved && typeof saved === 'object') return { image: saved.image ?? null, results: saved.results ?? {} }
  } catch {
    /* storage unavailable or corrupt */
  }
  return { image: null, results: {} }
}

export function ImageProvider({ children }) {
  const [state, setState] = useState(loadSession)

  useEffect(() => {
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state))
    } catch {
      /* ignore */
    }
  }, [state])

  const setImage = useCallback((image) => setState({ image, results: {} }), [])
  const clearImage = useCallback(() => setState({ image: null, results: {} }), [])
  const setResult = useCallback(
    (algorithm, result) => setState((s) => ({ ...s, results: { ...s.results, [algorithm]: result } })),
    [],
  )
  const updateResult = useCallback(
    (algorithm, patch) =>
      setState((s) =>
        s.results[algorithm]
          ? { ...s, results: { ...s.results, [algorithm]: { ...s.results[algorithm], ...patch } } }
          : s,
      ),
    [],
  )

  const value = useMemo(
    () => ({ ...state, setImage, clearImage, setResult, updateResult }),
    [state, setImage, clearImage, setResult, updateResult],
  )
  return <ImageContext.Provider value={value}>{children}</ImageContext.Provider>
}

export function useImage() {
  const context = useContext(ImageContext)
  if (!context) throw new Error('useImage must be used inside ImageProvider')
  return context
}
