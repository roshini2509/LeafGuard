import { NavLink, Link } from 'react-router-dom'
import { BookOpen, Columns2, Home, ImageUp, Layers } from 'lucide-react'
import Logo from './Logo.jsx'
import { useImage } from '../context/ImageContext.jsx'
import { apiUrl } from '../api/client.js'

const LINKS = [
  { to: '/', label: 'Home', icon: Home, end: true },
  { to: '/upload', label: 'Upload', icon: ImageUp },
  { to: '/algorithms', label: 'Algorithms', icon: Layers },
  { to: '/comparison', label: 'Comparison', icon: Columns2 },
  { to: '/learn', label: 'Learn', icon: BookOpen },
]

export default function Navbar() {
  const { image, results } = useImage()
  const processed = Object.keys(results).length
  return (
    <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/90 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center gap-4 px-4 py-3 sm:px-6 lg:px-8">
        <Link to="/" className="shrink-0">
          <Logo />
        </Link>
        <nav className="flex flex-1 items-center gap-1 overflow-x-auto">
          {LINKS.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-1.5 whitespace-nowrap rounded-lg px-3 py-2 text-sm font-medium transition ${
                  isActive ? 'bg-leaf-100 text-leaf-900' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                }`
              }
            >
              <Icon size={16} />
              <span className="hidden sm:inline">{label}</span>
            </NavLink>
          ))}
        </nav>
        {image && (
          <Link
            to="/upload"
            className="hidden items-center gap-2 rounded-xl border border-slate-200 py-1 pl-1 pr-3 md:flex"
            title="Current image"
          >
            <img src={apiUrl(image.original_url)} alt="" className="h-8 w-8 rounded-lg object-cover" />
            <span className="max-w-[9rem] truncate text-xs text-slate-600">{image.filename}</span>
            <span className="chip">{processed}/4</span>
          </Link>
        )}
      </div>
    </header>
  )
}
