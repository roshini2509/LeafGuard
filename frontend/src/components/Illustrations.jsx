// Small hand-drawn SVG illustrations for the algorithm cards.
// They are ILLUSTRATIONS (labelled as such), never algorithm output.

const LEAF = 'M20 92 C 20 40, 70 14, 128 16 C 126 70, 86 104, 20 92 Z'

export function KMeansIllustration() {
  return (
    <svg viewBox="0 0 150 110" className="h-full w-full">
      <defs>
        <clipPath id="km-leaf">
          <path d={LEAF} />
        </clipPath>
      </defs>
      <g clipPath="url(#km-leaf)">
        <rect width="150" height="110" fill="#4d9a3f" />
        <circle cx="62" cy="58" r="17" fill="#8a5a2b" />
        <circle cx="96" cy="38" r="10" fill="#c9b53d" />
        <circle cx="50" cy="80" r="8" fill="#8a5a2b" />
      </g>
      <path d={LEAF} fill="none" stroke="#14532d" strokeWidth="2" />
      {[[16, 18, '#4d9a3f'], [16, 34, '#8a5a2b'], [16, 50, '#c9b53d']].map(([x, y, c]) => (
        <rect key={y} x={x - 10} y={y - 10} width="12" height="12" rx="3" fill={c} stroke="white" strokeWidth="1.5" />
      ))}
    </svg>
  )
}

export function HSVIllustration() {
  const wedges = Array.from({ length: 24 }, (_, i) => i * 15)
  return (
    <svg viewBox="0 0 150 110" className="h-full w-full">
      <g transform="translate(75 55)">
        {wedges.map((angle) => {
          const a1 = ((angle - 90) * Math.PI) / 180
          const a2 = ((angle + 15 - 90) * Math.PI) / 180
          const selected = angle >= 15 && angle < 45
          const r = selected ? 47 : 42
          return (
            <path
              key={angle}
              d={`M0 0 L ${r * Math.cos(a1)} ${r * Math.sin(a1)} A ${r} ${r} 0 0 1 ${r * Math.cos(a2)} ${r * Math.sin(a2)} Z`}
              fill={`hsl(${angle} 75% 50%)`}
              opacity={selected ? 1 : 0.35}
            />
          )
        })}
        <circle r="18" fill="white" />
        <text textAnchor="middle" y="4" fontSize="10" fontWeight="600" fill="#14532d">
          H
        </text>
      </g>
    </svg>
  )
}

export function HistogramIllustration() {
  const before = [2, 4, 9, 22, 34, 26, 12, 5, 2, 1, 1, 1]
  const after = [10, 12, 11, 13, 12, 11, 13, 12, 11, 12, 13, 11]
  return (
    <svg viewBox="0 0 150 110" className="h-full w-full">
      {before.map((h, i) => (
        <rect key={`b${i}`} x={8 + i * 5} y={90 - h * 2} width="4" height={h * 2} rx="1" fill="#94a3b8" />
      ))}
      <path d="M72 55 h10 m-4 -4 l4 4 l-4 4" stroke="#14532d" strokeWidth="2" fill="none" />
      {after.map((h, i) => (
        <rect key={`a${i}`} x={86 + i * 5} y={90 - h * 2.6} width="4" height={h * 2.6} rx="1" fill="#166534" />
      ))}
      <line x1="6" y1="91" x2="144" y2="91" stroke="#cbd5e1" />
    </svg>
  )
}

export function CannyIllustration() {
  return (
    <svg viewBox="0 0 150 110" className="h-full w-full">
      <rect width="150" height="110" rx="10" fill="#0f172a" />
      <path d={LEAF} fill="none" stroke="white" strokeWidth="1.6" />
      <path d="M24 90 L 120 22" stroke="white" strokeWidth="1" opacity="0.8" />
      <circle cx="64" cy="58" r="12" fill="none" stroke="white" strokeWidth="1.4" />
      <circle cx="96" cy="40" r="7" fill="none" stroke="white" strokeWidth="1.2" />
    </svg>
  )
}

export const ILLUSTRATIONS = {
  kmeans: KMeansIllustration,
  hsv: HSVIllustration,
  histogram: HistogramIllustration,
  canny: CannyIllustration,
}
