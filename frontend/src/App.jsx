import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import Navbar from './components/Navbar.jsx'
import ErrorBoundary from './components/ErrorBoundary.jsx'
import Home from './pages/Home.jsx'
import Upload from './pages/Upload.jsx'
import Algorithms from './pages/Algorithms.jsx'
import Process from './pages/Process.jsx'
import Comparison from './pages/Comparison.jsx'
import Learn from './pages/Learn.jsx'

export default function App() {
  const location = useLocation()
  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="mx-auto max-w-7xl px-4 pb-16 pt-6 sm:px-6 lg:px-8">
        <ErrorBoundary key={location.pathname}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/algorithms" element={<Algorithms />} />
          <Route path="/process/:algorithm" element={<Process />} />
          <Route path="/comparison" element={<Comparison />} />
          <Route path="/learn" element={<Navigate to="/learn/kmeans" replace />} />
          <Route path="/learn/:algorithm" element={<Learn />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        </ErrorBoundary>
      </main>
      <footer className="border-t border-slate-200 bg-white py-6 text-center text-xs text-slate-500">
        LeafGuard · four classical image-processing algorithms implemented from scratch · results are approximate
        visual segmentations, not a plant-disease diagnosis.
      </footer>
    </div>
  )
}
