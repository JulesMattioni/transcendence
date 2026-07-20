import { Fragment, Children } from 'react'
import type { ReactNode } from 'react'
import Markdown from 'react-markdown'
import type { Source } from '../../api/rag'
import SourceMarker from './SourceMarker'

interface MessageContentProps {
  content: string
  sources: Source[] | null
  onOpenSource: (fileId: number) => void
}

function markersInString(
  text: string,
  sources: Source[] | null,
  onOpenSource: (fileId: number) => void,
) {
  const parts = text.split(/(\[\d+\])/g)
  return parts.map((part, i) => {
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
  })
}

function processChildren(
  children: ReactNode,
  sources: Source[] | null,
  onOpenSource: (fileId: number) => void,
) {
  return Children.map(children, (child, i) => {
    if (typeof child === 'string') {
      return (
        <Fragment key={i}>
          {markersInString(child, sources, onOpenSource)}
        </Fragment>
      )
    }
    return child
  })
}

function MessageContent({ content, sources, onOpenSource }: MessageContentProps) {
  return (
    <div className="prose-chat">
      <Markdown
        components={{
          p: ({ children }) => (
            <p>{processChildren(children, sources, onOpenSource)}</p>
          ),
          li: ({ children }) => (
            <li>{processChildren(children, sources, onOpenSource)}</li>
          ),
          h1: ({ children }) => (
            <h1 className="mt-3 mb-1 font-serif text-xl font-bold">
              {processChildren(children, sources, onOpenSource)}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="mt-3 mb-1 font-serif text-lg font-bold">
              {processChildren(children, sources, onOpenSource)}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="mt-2 mb-1 font-sans text-base font-semibold">
              {processChildren(children, sources, onOpenSource)}
            </h3>
          ),
        }}
      >
        {content}
      </Markdown>
    </div>
  )
}

export default MessageContent
