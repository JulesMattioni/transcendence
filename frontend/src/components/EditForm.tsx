import { useState } from 'react'
import { type FileRead, updateFile } from '../api/files'
import { ApiError } from '../api/client'

interface EditFormProps {
  file: FileRead
  onSuccess: () => void
}

function EditForm({ file, onSuccess }: EditFormProps) {
  const [title, setTitle] = useState(file.title)
  const [description, setDescription] = useState(file.description ?? '')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()

    if (!title.trim()) {
      setError('Please enter a title.')
      return
    }

    setSubmitting(true)
    setError(null)
    try {
      await updateFile(file.id, {
        title,
        description: description || undefined,
      })
      onSuccess()
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Update failed.'
      setError(message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="mb-1 block text-sm font-medium text-black">
          Title
        </label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="w-full border border-gray-300 px-3 py-2"
          placeholder="My document"
        />
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium text-black">
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
        {submitting ? 'Saving…' : 'Save'}
      </button>
    </form>
  )
}

export default EditForm
