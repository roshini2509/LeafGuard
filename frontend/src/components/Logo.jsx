export default function Logo({ size = 34, withText = true }) {
  return (
    <span className="flex items-center gap-2">
      <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true">
        <rect width="32" height="32" rx="9" fill="#14532d" />
        <path d="M8.5 23.5c0-9.2 6.2-14.6 15.5-15.5-.9 9.3-6.3 15.5-15.5 15.5z" fill="#86efac" />
        <path d="M8.5 23.5l9.3-9.3" stroke="#14532d" strokeWidth="1.6" strokeLinecap="round" />
        <circle cx="19.5" cy="12.5" r="1.6" fill="#14532d" />
      </svg>
      {withText && (
        <span className="text-lg font-bold tracking-tight text-leaf-900">
          Leaf<span className="text-leaf-600">Guard</span>
        </span>
      )}
    </span>
  )
}
