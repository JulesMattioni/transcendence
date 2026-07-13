import DashboardLayout from '../../components/dashboard/DashboardLayout'
import { useState, useEffect } from 'react'
import { type FileRead, listFiles } from '../../api/files'
import { ApiError } from '../../api/client'
import Modal from '../../components/Modal'
import { Plus } from 'lucide-react'

function FilesPage() {
  const [files, setFiles] = useState<FileRead[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)

  useEffect(() => {
    listFiles()
    .then((data) => setFiles(data))
    .catch((err) => {
      const message =
        err instanceof ApiError ? err.message : 'Could not load files.'
      setError(message)
    })
    .finally(() => setLoading(false))
  }, [])

    return (
    <DashboardLayout>
      <div className="flex items-center justify-between">
        <h1 className="font-serif text-2xl font-bold text-ink">Files</h1>
        <button
          onClick={() => setIsModalOpen(true)}
          className="inline-flex items-center gap-2 bg-keepr px-4 py-2 font-medium text-white transition-colors duration-200 hover:bg-blue-700"
        >
          Add file <Plus size={15} strokeWidth={2}/>
        </button>
      </div>


      {loading && <p className="mt-4 text-muted">Loading…</p>}

      {error && <p className="mt-4 text-red-600">{error}</p>}

      {!loading && !error && files.length === 0 && (
        <p className="mt-4 text-muted">No files yet.</p>
      )}

      {!loading && !error && files.length > 0 && (
        <ul className="mt-4 space-y-2">
          {files.map((file) => (
            <li
              key={file.id}
              className="border border-gray-200 p-3"
            >
              <p className="font-medium text-ink">{file.title}</p>
              <p className="text-sm text-muted">
                {file.filename} · {file.size_bytes} bytes
              </p>
            </li>
          ))}
        </ul>
      )}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Add file"
      >
        <p className="text-muted">Upload form goes here.</p>
      </Modal>

    </DashboardLayout>
  )

}

export default FilesPage
