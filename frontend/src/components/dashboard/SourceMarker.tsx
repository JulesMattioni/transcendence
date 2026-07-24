import { useState } from 'react'
import type { Source } from '../../api/rag'

interface SourceMarkerProps {
  index: number
  source: Source | undefined
  onOpen: (fileId: number) => void
}

/**
 * Inline citation marker in an assistant answer. Renders a clickable
 * badge that opens the cited file and reveals its excerpt on hover;
 * falls back to plain "[n]" text when the source is unknown.
 */
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
        <span className="absolute top-full left-1/2 z-50 mt-1 w-64 -translate-x-1/2 rounded bg-white p-2 text-xs text-muted shadow-lg ring-1 ring-black/5">
          {source.excerpt}
        </span>
      )}
    </span>
  )
}

export default SourceMarker
