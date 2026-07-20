import { Fragment } from 'react'
import type { Source } from '../../api/rag'
import SourceMarker from './SourceMarker'

interface MessageContentProps {
  content: string
  sources: Source[] | null
  onOpenSource: (fileId: number) => void
}

function MessageContent({ content, sources, onOpenSource }: MessageContentProps) {
  const parts = content.split(/(\[\d+\])/g)

  return (
    <>
      {parts.map((part, i) => {
        const match = part.match(/^\[(\d+)\]$/)
        if (match) {
          const n = parseInt(match[1], 10)
          return (
            <SourceMarker
              key={i}
              index={n}
              source={sources?.[n - 1]}
              onOpen={onOpenSource}
            />
          )
        }
        return <Fragment key={i}>{part}</Fragment>
      })}
    </>
  )
}

export default MessageContent
