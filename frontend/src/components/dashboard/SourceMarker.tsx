import { useState } from 'react'
import type { Source } from '../../api/rag'

interface SourceMarkerProps {
  index: number
  source: Source | undefined
  onOpen: (fileId: number) => void
}

function SourceMarker({ index, source, onOpen }: SourceMarkerProps) {
  const [hovered, setHovered] = useState(false)

  if (!source) return <span>[{index}]</span>

  return (
    <span
      className="relative"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <button
        type="button"
        onClick={() => onOpen(source.file_id)}
        className="mx-0.5 inline-flex items-center justify-center rounded bg-blue-100 px-1 text-xs font-medium text-keepr hover:bg-keepr hover:text-white"
      >
        {index}
      </button>

      {hovered && (
        <span className="absolute top-full left-1/2 z-50 mt-1 w-64 -translate-x-1/2 border border-gray-200 bg-white p-2 text-xs text-muted shadow-lg">
          {source.excerpt}
        </span>
      )}
    </span>
  )
}

export default SourceMarker
