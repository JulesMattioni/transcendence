import { useEffect, useState } from 'react'
import { type FileRead, fetchFileContent } from '../api/files'

/**
 * Preview a file inline by fetching its content as a blob URL and
 * rendering it by type: image, PDF iframe, text, or a download link as a
 * fallback. Revokes the blob URL on unmount.
 */
function FilePreview({ file }: { file: FileRead }) {
  const [url, setUrl] = useState<string | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    let objectUrl: string | null = null
    let cancelled = false

    fetchFileContent(file.id)
      .then((blob) => {
        if (cancelled) return
        objectUrl = URL.createObjectURL(blob)
        setUrl(objectUrl)
      })
      .catch((err) => {
        console.error('FilePreview fetch failed:', err)
        if (!cancelled) setError(true)
      })

    return () => {
      cancelled = true
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [file.id])

  if (error) return <p className="text-red-600">Could not load preview.</p>
  if (!url) return <p className="text-muted">Loading preview…</p>

  const type = file.content_type

  if (type.startsWith('image/')) {
    return (
      <img
        src={url}
        alt={file.title}
        className="mx-auto max-h-[70vh] max-w-full rounded object-contain"
      />
    )
  }

  if (type === 'application/pdf') {
    return <iframe src={url} title={file.title} className="h-[70vh] w-full rounded" />
  }

  if (type.startsWith('text/')) {
    return <TextPreview url={url} />
  }

  return (
    <a
      href={url}
      download={file.filename}
      className="inline-block rounded bg-keepr px-4 py-2 font-medium text-white transition-colors hover:bg-blue-700"
    >
      Download {file.filename}
    </a>
  )
}

/** Fetch a text blob URL and render its contents in a scrollable block. */
function TextPreview({ url }: { url: string }) {
  const [text, setText] = useState('')
  useEffect(() => {
    fetch(url)
      .then((r) => r.text())
      .then(setText)
  }, [url])
  return (
    <pre className="max-h-[70vh] overflow-auto rounded bg-gray-50 p-3 text-sm">
      {text}
    </pre>
  )
}

export default FilePreview
