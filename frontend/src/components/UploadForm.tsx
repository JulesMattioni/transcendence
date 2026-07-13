import { useState } from 'react'
import { uploadFile } from '../api/files'
import { ApiError } from '../api/client'


interface UploadFormProps {
  onSuccess: () => void
}

function UploadForm({ onSuccess }: UploadFormProps) {
  const [file, setFile] = useState<File | null>(null)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [isDragging, setIsDragging] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)


  function handleDrop(e: React.DragEvent) {
    e.preventDefault()
    setIsDragging(false)
    const dropped = e.dataTransfer.files?.[0]
    if (dropped) {
      setFile(dropped)
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()

    if (!file) {
      setError('Please choose a file.')
      return
    }
    if (!title.trim()) {
      setError('Please enter a title.')
      return
    }

    setSubmitting(true)
    setError(null)
    try {
      await uploadFile(file, title, description || undefined)
      onSuccess()
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : 'Upload failed.'
      setError(message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
  <form onSubmit={handleSubmit} className="space-y-4">
      {/* File input */}

    <div>
        <label className="mb-1 block text-sm font-medium text-ink">File</label>
        <label
          onDragOver={(e) => {
            e.preventDefault()
            setIsDragging(true)
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          className={`flex cursor-pointer flex-col items-center justify-center border-2 border-dashed p-6 text-center text-sm transition-colors ${
            isDragging
              ? 'border-keepr bg-blue-50 text-keepr'
              : 'border-gray-300 text-muted'
          }`}
        >
          {file ? (
            <span className="font-medium text-ink">{file.name}</span>
          ) : (
            <span>Drag a file here, or click to browse</span>
          )}
          <input
            type="file"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="hidden"
          />
        </label>
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium text-ink">Title</label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="w-full border border-gray-300 px-3 py-2"
          placeholder="My document"
        />
      </div>


      <div>
        <label className="mb-1 block text-sm font-medium text-ink">
          Description <span className="text-muted">(optional)</span>
        </label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="w-full border border-gray-300 px-3 py-2"
          rows={3}
        />
      </div>

      {error && <p className="text-sm text-red-500">{error}</p>}

      <button
        type="submit"
        disabled={submitting}
        className="w-full bg-keepr px-4 py-2 font-medium text-white disabled:opacity-50"
      >
        {submitting ? 'Uploading…' : 'Upload'}
      </button>

    </form>
  )
}

export default UploadForm
